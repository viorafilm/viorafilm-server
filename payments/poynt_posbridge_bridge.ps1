param(
    [Parameter(Mandatory = $true)]
    [string]$Command,
    [Parameter(Mandatory = $true)]
    [string]$PayloadPath,
    [Parameter(Mandatory = $true)]
    [string]$SdkDir
)

$ErrorActionPreference = "Stop"

function Write-JsonResult {
    param([hashtable]$Payload)
    $Payload | ConvertTo-Json -Depth 8 -Compress
}

function New-Logger {
    param(
        [System.Reflection.Assembly]$Assembly,
        [string]$BaseDir
    )
    $loggerDir = Join-Path $BaseDir "logs"
    New-Item -ItemType Directory -Force -Path $loggerDir | Out-Null
    $loggerFactory = $Assembly.GetType("PoyntPOSBridge.LoggerFactory")
    $loggingLevel = $Assembly.GetType("PoyntPOSBridge.LoggingLevel")
    $debugLevel = [Enum]::Parse($loggingLevel, "DEBUG")
    return $loggerFactory::CreateFileLogger("poynt_posbridge", $debugLevel, $loggerDir)
}

function New-PoyntApi {
    param(
        [System.Reflection.Assembly]$Assembly,
        [object]$Payload
    )
    $logger = New-Logger -Assembly $Assembly -BaseDir (Split-Path -Parent $SdkDir)
    $apiType = $Assembly.GetType("PoyntPOSBridge.PoyntPOSApi")
    $api = New-Object $apiType ([string]$Payload.terminal_ip, $logger)
    $api.DefaultTimeoutInMs = [int]($Payload.request_timeout_ms | ForEach-Object { if ($_ -eq $null) { 60000 } else { $_ } })
    $key = [string]($Payload.pairing_code_or_key | ForEach-Object { if ($_ -eq $null) { "" } else { $_ } })
    if (-not [string]::IsNullOrWhiteSpace($key)) {
        $api.Key = $key
    }
    return $api
}

function New-SaleRequest {
    param(
        [System.Reflection.Assembly]$Assembly,
        [object]$Payload
    )
    $requestType = $Assembly.GetType("PoyntPOSBridge.AuthorizeSalesRequest")
    $request = $requestType::Create(
        [int]($Payload.request_timeout_ms | ForEach-Object { if ($_ -eq $null) { 60000 } else { $_ } }),
        [string]($Payload.currency | ForEach-Object { if ($_ -eq $null) { "CAD" } else { $_ } }),
        [int]$Payload.amount_cents
    )
    $payment = $request.Payment
    $payment.OrderId = [string]$Payload.order_id
    $payment.ReferenceId = [string]$Payload.order_id
    $payment.Notes = [string]$Payload.description
    $payment.SkipReceiptScreen = -not [bool]$Payload.auto_print_receipt
    $payment.SkipSignatureScreen = $false
    $payment.ManualEntry = $false

    $itemType = $Assembly.GetType("PoyntPOSBridge.OrderItem")
    $orderItem = New-Object $itemType
    $orderItem.Name = [string]($Payload.description | ForEach-Object { if ([string]::IsNullOrWhiteSpace($_)) { "Photo kiosk order" } else { $_ } })
    $orderItem.Quantity = 1
    $orderItem.Tax = 0
    $orderItem.Status = "ORDERED"
    $orderItem.UnitOfMeasure = "EACH"
    $orderItem.UnitPrice = [int]$Payload.amount_cents
    $payment.Order.Items.Add($orderItem)
    $payment.Order.Notes = [string]$Payload.description
    return $request
}

function Convert-PaymentResponse {
    param(
        [object]$Response
    )
    $payment = $Response.Payment
    $transaction = $null
    if ($payment -and $payment.Transactions -and $payment.Transactions.Count -gt 0) {
        $transaction = $payment.Transactions[0]
    }
    $processorResponse = $null
    if ($transaction -and $transaction.ProcessorResponse) {
        $processorResponse = $transaction.ProcessorResponse
    }
    $card = $null
    if ($transaction -and $transaction.FundingSource -and $transaction.FundingSource.Card) {
        $card = $transaction.FundingSource.Card
    }
    return @{
        success = $true
        raw_payment_status = [string]($payment.Status)
        provider_transaction_id = [string]($transaction.Id)
        provider_reference = [string]($processorResponse.RetrievalRefNum)
        transaction_number = [string]($transaction.TransactionNumber)
        processor_transaction_id = [string]($processorResponse.TransactionId)
        approval_code = [string]($processorResponse.ApprovalCode)
        processor_status = [string]($processorResponse.Status)
        processor_status_message = [string]($processorResponse.StatusMessage)
        card_brand = [string]($card.Type)
        last4_masked = [string]($card.NumberLast4)
        message = [string]($payment.Status)
    }
}

try {
    $sdkPath = Resolve-Path $SdkDir
    $payload = Get-Content -Path $PayloadPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $dllPath = Join-Path $sdkPath "PoyntPOSBridge.dll"
    $jsonDll = Join-Path $sdkPath "Newtonsoft.Json.dll"
    $restSharpDll = Join-Path $sdkPath "RestSharp.dll"

    if (-not (Test-Path $dllPath)) {
        throw "PoyntPOSBridge.dll not found at $dllPath"
    }
    if (Test-Path $jsonDll) {
        [void][System.Reflection.Assembly]::LoadFrom($jsonDll)
    }
    if (Test-Path $restSharpDll) {
        [void][System.Reflection.Assembly]::LoadFrom($restSharpDll)
    }
    $assembly = [System.Reflection.Assembly]::LoadFrom($dllPath)

    switch ($Command.ToLowerInvariant()) {
        "pair" {
            $api = New-PoyntApi -Assembly $assembly -Payload $payload
            $requestType = $assembly.GetType("PoyntPOSBridge.PairDeviceWithKeyRequest")
            $pairingType = $assembly.GetType("PoyntPOSBridge.PairingRequest")
            $request = New-Object $requestType
            $request.PairingRequest = New-Object $pairingType
            $request.PairingRequest.PairingCode = [string]$payload.pairing_code_or_key
            $deviceName = [string]($payload.terminal_name | ForEach-Object { if ([string]::IsNullOrWhiteSpace($_)) { "External POS System" } else { $_ } })
            $response = $api.PairDeviceWithKey($deviceName, $request)
            Write-JsonResult @{
                success = (-not [string]::IsNullOrWhiteSpace([string]$response.PairingCode))
                pairing_code = [string]$response.PairingCode
                timed_out = [bool]$response.TimedOut
                errors = $response.Error
                message = if (-not [string]::IsNullOrWhiteSpace([string]$response.PairingCode)) { "Pair succeeded" } else { "Pair failed" }
            }
            break
        }
        "ping" {
            $api = New-PoyntApi -Assembly $assembly -Payload $payload
            $success = [bool]$api.PingDevice()
            Write-JsonResult @{
                success = $success
                message = if ($success) { "Ping succeeded" } else { "Ping failed" }
            }
            break
        }
        "sale" {
            $api = New-PoyntApi -Assembly $assembly -Payload $payload
            $request = New-SaleRequest -Assembly $assembly -Payload $payload
            $response = $api.AuthorizeSales($request)
            Write-JsonResult (Convert-PaymentResponse -Response $response)
            break
        }
        "void" {
            $api = New-PoyntApi -Assembly $assembly -Payload $payload
            $requestType = $assembly.GetType("PoyntPOSBridge.AuthorizeVoidRequest")
            $request = New-Object $requestType
            $request.TransactionId = [string]$payload.transaction_id
            $request.Timeout = [int]($payload.request_timeout_ms | ForEach-Object { if ($_ -eq $null) { 60000 } else { $_ } })
            $response = $api.AuthorizeVoid($request)
            Write-JsonResult (Convert-PaymentResponse -Response $response)
            break
        }
        "refund" {
            $api = New-PoyntApi -Assembly $assembly -Payload $payload
            $requestType = $assembly.GetType("PoyntPOSBridge.AuthorizeRefundRequest")
            $refundPaymentType = $assembly.GetType("PoyntPOSBridge.RefundPayment")
            $request = New-Object $requestType
            $request.TransactionId = [string]$payload.transaction_id
            $request.Timeout = [int]($payload.request_timeout_ms | ForEach-Object { if ($_ -eq $null) { 60000 } else { $_ } })
            $request.Payment = New-Object $refundPaymentType
            $request.Payment.Amount = [int]$payload.amount_cents
            $response = $api.AuthorizeRefund($request)
            Write-JsonResult (Convert-PaymentResponse -Response $response)
            break
        }
        "flow" {
            $api = New-PoyntApi -Assembly $assembly -Payload $payload
            $response = $api.GetPaymentFlowState()
            Write-JsonResult @{
                success = $true
                current_state = [string]$response.CurrentState
                message = [string]$response.CurrentState
            }
            break
        }
        default {
            throw "Unsupported command: $Command"
        }
    }
}
catch {
    Write-JsonResult @{
        success = $false
        error = [string]$_.Exception.Message
        message = [string]$_.Exception.Message
    }
    exit 1
}
