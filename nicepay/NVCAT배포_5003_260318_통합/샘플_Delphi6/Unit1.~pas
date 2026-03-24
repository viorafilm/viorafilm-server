unit Unit1;

interface

uses
  Windows, Messages, SysUtils, Variants, Classes, Graphics, Controls, Forms,
  Dialogs, StdCtrls;

type
  TForm1 = class(TForm)
    GroupBox1: TGroupBox;
    Label1: TLabel;
    ComboDeal: TComboBox;
    Label2: TLabel;
    ComboHalbu: TComboBox;
    Label3: TLabel;
    Label4: TLabel;
    EditMoney: TEdit;
    EditAgreenum: TEdit;
    Label5: TLabel;
    Label6: TLabel;
    EditAgreedate: TEdit;
    EditTax: TEdit;
    Label7: TLabel;
    EditBongsa: TEdit;
    CheckKeyin: TCheckBox;
    Label8: TLabel;
    EditCatid: TEdit;
    ButtonReq: TButton;
    ButtonCnl: TButton;
    GroupBox2: TGroupBox;
    EditRecvdata: TEdit;
    Label9: TLabel;
    Label10: TLabel;
    Label11: TLabel;
    Label12: TLabel;
    Label13: TLabel;
    textBox17: TEdit;
    textBox13: TEdit;
    textBox9: TEdit;
    textBox5: TEdit;
    textBox1: TEdit;
    Label14: TLabel;
    Label15: TLabel;
    Label16: TLabel;
    Label17: TLabel;
    textBox14: TEdit;
    textBox10: TEdit;
    textBox6: TEdit;
    textBox2: TEdit;
    Label18: TLabel;
    Label19: TLabel;
    Label20: TLabel;
    Label21: TLabel;
    Label22: TLabel;
    textBox15: TEdit;
    textBox18: TEdit;
    textBox11: TEdit;
    textBox7: TEdit;
    textBox3: TEdit;
    Label23: TLabel;
    Label24: TLabel;
    Label25: TLabel;
    Label26: TLabel;
    Label27: TLabel;
    textBox12: TEdit;
    textBox16: TEdit;
    textBox19: TEdit;
    textBox8: TEdit;
    textBox4: TEdit;
    GroupBox3: TGroupBox;
    Label28: TLabel;
    EditSend: TEdit;
    Label29: TLabel;
    EditRecv: TEdit;
    ButtonNICEVCAT: TButton;
    ButtonRestart: TButton;
    ButtonReset: TButton;
    EditWaittime: TEdit;
    Label30: TLabel;
    Label31: TLabel;
    Label32: TLabel;
    ComboBilltp: TComboBox;
    Label33: TLabel;
    ComboBillMoney: TComboBox;
    Label34: TLabel;
    Billno: TEdit;
    Label35: TLabel;
    Billdt: TEdit;
    Label36: TLabel;
    billsn: TEdit;
    Label37: TLabel;
    billamt: TEdit;
    Label38: TLabel;
    Billserial: TEdit;
    Button1: TButton;
    Label39: TLabel;
    EditCashno: TEdit;
    Button2: TButton;
    Label40: TLabel;
    SignData: TEdit;
    Button3: TButton;
    Button4: TButton;
    Button5: TButton;
    Label41: TLabel;
    Label42: TLabel;
    Label43: TLabel;
    EditNiceDownYN: TEdit;
    EditCustomCnl: TEdit;
    Button6: TButton;
    Button7: TButton;
    Button8: TButton;
    procedure ButtonReqClick(Sender: TObject);
    procedure FormCreate(Sender: TObject);
    procedure ButtonCnlClick(Sender: TObject);
    procedure ButtonNICEVCATClick(Sender: TObject);
    procedure ButtonResetClick(Sender: TObject);
    procedure ButtonRestartClick(Sender: TObject);
    procedure ComboDealSelect(Sender: TObject);
    procedure Button1Click(Sender: TObject);
    procedure Button2Click(Sender: TObject);
    procedure Button3Click(Sender: TObject);
    procedure Button4Click(Sender: TObject);
    procedure Button5Click(Sender: TObject);
    procedure Button6Click(Sender: TObject);
    procedure Button7Click(Sender: TObject);
    procedure Button8Click(Sender: TObject);
  private
    { Private declarations }
  public
    { Public declarations }
  end;

  function mNICEVCAT(SendData:String;  RecvData:PChar) : Integer;  stdcall;  external 'NVCAT.dll' name 'NICEVCAT';
  function mREQ_STOP() : Integer;  stdcall;  external 'NVCAT.dll' name 'REQ_STOP';
  function mRESTART() : Integer;  stdcall;  external 'NVCAT.dll' name 'RESTART';
  function mREADER_RESET(time:String) : Integer;  stdcall;  external 'NVCAT.dll' name 'READER_RESET';
  function mCHK_CASHIC_MP() : Integer;  stdcall;  external 'NVCAT.dll' name 'CHK_CASHIC_MP';
  function mCHK_CARDIN_MP(RecvData:PChar) : Integer;  stdcall;  external 'NVCAT.dll' name 'CHK_CARDIN_MP';
  function mREQ_BARCODE(hwtype:String; RecvData:PChar) : Integer;  stdcall;  external 'NVCAT.dll' name 'REQ_BARCODE';
  function mCHK_CASHIC2() : Integer;  stdcall;  external 'NVCAT.dll' name 'CHK_CASHIC2';
  function mNVCATSHUTDOWN() : Integer;  stdcall;  external 'NVCAT.dll' name 'NVCATSHUTDOWN';  
  function mSetCnlDisableYN(NiceDownYN:String; CustomCnl:String) : Integer;  stdcall;  external 'NVCAT.dll' name 'SetCnlDisableYN';
  function mGetMac(MAC:PChar) : Integer;  stdcall;  external 'NVCAT.dll' name 'GetMac';
  function mREQ_TITLOCK() : Integer;  stdcall;  external 'NVCAT.dll' name 'REQ_TITLOCK';
  
var
  Form1: TForm1;
  FS : String;
  ret : Integer;

implementation

{$R *.dfm}

procedure TForm1.ButtonReqClick(Sender: TObject);
var
        Halbu : String;
        SendBuf, RecvData, Billtpcd, Billmoneycd : String;
        RecvBuf : PChar;
        i, j, k : Integer;
begin
        FS := char($1C);
        Halbu := ComboHalbu.Items.Strings[ComboHalbu.ItemIndex];

        RecvBuf := Nil;
        RecvBuf := AllocMem(2480);

        case comboDeal.ItemIndex of
        0: //신용승인
                begin
                        SendBuf := '0200' + FS + '10' + FS + 'C' + FS + EditMoney.Text + FS + EditTax.Text + FS + EditBongsa.Text + FS + Halbu + FS + '' + FS + '' + FS + EditCatid.Text + FS;
                end;
        1: //FALLBACK
                begin
                        SendBuf := '0200' + FS + '10' + FS + 'F' + FS + EditMoney.Text + FS + EditTax.Text + FS + EditBongsa.Text + FS + Halbu + FS + '' + FS + '' + FS + EditCatid.Text + FS;
                end;
        2: //신용취소
                begin
                        SendBuf := '0420' + FS + '10' + FS + 'C' + FS + EditMoney.Text + FS + EditTax.Text + FS + EditBongsa.Text + FS + Halbu + FS + EditAgreenum.Text + FS + EditAgreedate.Text + FS + EditCatid.Text + FS;
                end;
        3: //현금승인
                begin
                        Halbu := Copy(ComboHalbu.Items.Strings[ComboHalbu.ItemIndex], 1, 2);
                        if CheckKeyin.Checked = false then
                                begin
                                        SendBuf := '0200' + FS + '21' + FS + 'C' + FS + EditMoney.Text + FS + EditTax.Text + FS + EditBongsa.Text + FS + Halbu + FS + '' + FS + '' + FS + EditCatid.Text + FS;
                                end
                        else
                                begin
                                        SendBuf := '0200' + FS + '21' + FS + 'K' + FS + EditMoney.Text + FS + EditTax.Text + FS + EditBongsa.Text + FS + Halbu + FS + '' + FS + '' + FS + EditCatid.Text + FS;
                                end;
                end;
        4: //현금취소
                begin
                        Halbu := Copy(ComboHalbu.Items.Strings[ComboHalbu.ItemIndex], 1, 2);
                        if CheckKeyin.Checked = false then
                                begin
                                        SendBuf := '0420' + FS + '21' + FS + 'C' + FS + EditMoney.Text + FS + EditTax.Text + FS + EditBongsa.Text + FS + Halbu + FS + EditAgreenum.Text + FS + EditAgreedate.Text + FS + EditCatid.Text + FS;
                                end
                        else
                                begin
                                        SendBuf := '0420' + FS + '21' + FS + 'K' + FS + EditMoney.Text + FS + EditTax.Text + FS + EditBongsa.Text + FS + Halbu + FS + EditAgreenum.Text + FS + EditAgreedate.Text + FS + EditCatid.Text + FS;
                                end;
                end;
        5: //은련승인
                begin
                        SendBuf := '0200' + FS + 'UP' + FS + 'C' + FS + EditMoney.Text + FS + EditTax.Text + FS + EditBongsa.Text + FS + Halbu + FS + '' + FS + '' + FS + EditCatid.Text + FS;
                end;
        6: //은련취소
                begin
                        SendBuf := '0420' + FS + 'UP' + FS + 'C' + FS + EditMoney.Text + FS + EditTax.Text + FS + EditBongsa.Text + FS + Halbu + FS + EditAgreenum.Text + FS + EditAgreedate.Text + FS + EditCatid.Text + FS;
                end;
        7: //수표조회
                begin
                        Billtpcd := copy(ComboBilltp.Text, 1, 2);
                        Billmoneycd := copy(ComboBillMoney.Text, 1, 2);
                        SendBuf := '0200' + FS + '20' + FS + 'K' + FS + Billtpcd + FS + Billmoneycd + FS + Billno.Text + FS + Billdt.Text + FS + billsn.Text + FS + billamt.Text + FS + Billserial.Text + FS;
                end;
        8: //현금IC승인
                begin
                        SendBuf := '0200' + FS + 'I1' + FS + '00' + FS + EditBongsa.Text + FS + EditTax.Text + FS + EditMoney.Text + FS + FS + FS + '' + FS + FS + FS + FS + '' + FS + FS + FS + FS + FS;
                end;
        9: //현금IC취소
                begin
                        SendBuf := '0420' + FS + 'I4' + FS + '00' + FS + EditBongsa.Text + FS + EditTax.Text + FS + EditMoney.Text + FS + EditAgreenum.Text + FS + EditAgreedate.Text + FS + FS + FS + FS + FS + '' + FS + FS + FS + FS + FS;
                end;
        10: //현금IC승인(멀티패드)
                begin
                        SendBuf := '0200' + FS + 'I1' + FS + '04' + FS + EditBongsa.Text + FS + EditTax.Text + FS + EditMoney.Text + FS + FS + FS + '' + FS + FS + FS + FS + '' + FS + FS + FS + FS + FS;
                end;
        11: //현금IC취소(멀티패드)
                begin
                        SendBuf := '0420' + FS + 'I4' + FS + '04' + FS + EditBongsa.Text + FS + EditTax.Text + FS + EditMoney.Text + FS + EditAgreenum.Text + FS + EditAgreedate.Text + FS + FS + FS + FS + FS + '' + FS + FS + FS + FS + FS;
                end;
        12: //그린카드적립승인
                begin
                        SendBuf := '0320' + FS + '48' + FS + 'I' + FS + EditMoney.Text + FS + EditTax.Text + FS + EditBongsa.Text + FS + FS + '' + FS + '' + FS + EditCatid.Text + FS + FS + FS + FS + FS + FS + FS + FS + '' + FS + FS + 'HPS' + FS + '' + FS + EditCashno.Text + FS + FS + FS + FS + FS + FS + FS;
                end;
        13: //그린카드적립취소
                begin
                        SendBuf := '0540' + FS + '48' + FS + 'I' + FS + EditMoney.Text + FS + EditTax.Text + FS + EditBongsa.Text + FS + FS + EditAgreenum.Text + FS + EditAgreedate.Text + FS + EditCatid.Text + FS + FS + FS + FS + FS + FS + FS + FS + '' + FS + FS + 'HPS' + FS + '' + FS + EditCashno.Text + FS + FS + FS + FS + FS + FS + FS;
                end;
        14: //DCC환율조회(POS 2TR)
                begin
                        SendBuf := '0200' + FS + 'D1' + FS + 'C' + FS + EditMoney.Text + FS + EditTax.Text + FS + EditBongsa.Text + FS + Halbu + FS + FS + FS + EditCatid.Text + FS + '410' + FS + EditMoney.Text + FS + '0' + FS + FS + EditCashno.Text + FS + FS + FS + FS + '' + FS + SignData.Text + FS + FS + FS + FS + FS;
                end;
        15: //DCC원화통화승인(POS 2TR)
                begin
                        SendBuf := '0200' + FS + 'D2' + FS + 'C' + FS + EditMoney.Text + FS + EditTax.Text + FS + EditBongsa.Text + FS + Halbu + FS + FS + FS + EditCatid.Text + FS + '410' + FS + EditMoney.Text + FS + '0' + FS + FS + EditCashno.Text + FS + FS + FS + FS + '' + FS + SignData.Text + FS + FS + FS + FS + FS;
                end;
        16: //DCC자국통화승인(POS 2TR)
                begin
                        SendBuf := '0200' + FS + 'D3' + FS + 'C' + FS + EditMoney.Text + FS + EditTax.Text + FS + EditBongsa.Text + FS + Halbu + FS + FS + FS + EditCatid.Text + FS + '410' + FS + EditMoney.Text + FS + '0' + FS + FS + EditCashno.Text + FS + FS + FS + FS + '' + FS + SignData.Text + FS + FS + FS + FS + FS;
                end;
        17: //무카드신용부분취소 (LJY20220224)
                begin
                        ShowMessage('취소할 금액/원거래 승인번호/원거래 승인날짜/거래일련번호/원거래 금액/전문TEXT PCL 전문 구성 필요');
                        SendBuf := '0520' + FS + '30' + FS + 'N' + FS + EditMoney.Text + FS + EditTax.Text + FS + EditBongsa.Text + FS + Halbu + FS + EditAgreenum.Text + FS + EditAgreedate.Text + FS + EditCatid.Text + FS + FS + FS + EditCashno.Text + FS + FS + FS + FS + FS + '' + FS + 'P000000001004' + FS + 'PCL' + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS;
                end;
        end;

        ret := mNICEVCAT(SendBuf, RecvBuf);
        ShowMessage('ret : ' + IntToStr(ret)); //리턴값 처리 꼭 해주세요.


        if ret <> 1 then
                begin
                        Exit;
                        //Form1.Close;
                end;
        EditRecvdata.Text := StrPas(RecvBuf);

        if ComboDeal.ItemIndex = 7 then
                begin
                        Exit;
                        //Form1.Close;
                end;


        //=============================================================================================


        i := 1;
        j := 0;
        k := 1;
        RecvData := EditRecvdata.Text;

        if (ComboDeal.ItemIndex = 8) or (ComboDeal.ItemIndex = 9) or (ComboDeal.ItemIndex = 10) or (ComboDeal.ItemIndex = 11) then
        begin
        while true do
        begin
                if CompareStr(Copy(RecvData, i, 1), FS) = 0 then
                begin
                        j := j + 1;

                        case j of
                                1: //거래구분
                                        begin
                                        textBox1.Text := copy(RecvData, k, i-k);
                                        end;
                                2: //거래유형
                                        begin
                                        textBox2.Text := copy(RecvData, k, i-k);
                                        end;
                                3: //응답코드
                                        begin        
                                        textBox3.Text := copy(RecvData, k, i-k);
                                        end;
                                4: //봉사료               
                                        begin
                                        textBox6.Text := copy(RecvData, k, i-k);
                                        end;
                                5: //세금
                                        begin
                                        textBox5.Text := copy(RecvData, k, i-k);
                                        end;
                                6: //거래금액
                                        begin
                                        textBox4.Text := copy(RecvData, k, i-k);
                                        end;
                                7: //가맹점번호
                                        begin
                                        textBox14.Text := copy(RecvData, k, i-k);
                                        end;
                                8: //승인일시
                                        begin
                                        textBox9.Text := copy(RecvData, k, i-k);
                                        end;
                                9: //승인번호
                                        begin
                                        textBox8.Text := copy(RecvData, k, i-k); 
                                        EditAgreenum.Text := textBox8.Text;
                                        end;
                                10: //발급 코드
                                        begin
                                        textBox10.Text := copy(RecvData, k, i-k);
                                        end;
                                11: //발급명
                                        begin
                                        textBox11.Text := copy(RecvData, k, i-k);
                                        end;
                                12: //발급기관점별코드
                                        begin
                                        end;
                                13: //매입 코드
                                        begin
                                        textBox12.Text := copy(RecvData, k, i-k);
                                        end;
                                14: //매입명
                                        begin
                                        textBox13.Text := copy(RecvData, k, i-k);
                                        end;
                                15: //매입기관점별코드
                                        begin
                                        //textBox7.Text := copy(RecvData, k, i-k);
                                        end;
                                16: //수수료율
                                        begin
                                        end;
                                17: //가맹점수수료
                                        begin
                                        end;
                                18: //발급기관 수수료
                                        begin
                                        end;
                                19: //매입기관 수수료
                                        begin
                                        end;
                                20: //출금계좌번호
                                        begin
                                        textBox18.Text := copy(RecvData, k, i-k);
                                        end;
                                21: //원장잔액부호
                                        begin
                                        textBox19.Text := copy(RecvData, k, i-k);
                                        end;
                                22: //원장잔액
                                        begin
                                        textBox16.Text := copy(RecvData, k, i-k);
                                        end;
                                23: //출금가능금액
                                        begin
                                        textBox15.Text := copy(RecvData, k, i-k);
                                        end;
                                24: //응답메세지
                                        begin
                                        textBox17.Text := copy(RecvData, k, i-k);
                                        end;
                        end;
                        k := i + 1;

                        if j = 24 then
                        begin
                                break;
                        end;
                end;
                i := i + 1;      
        end;
        end
        else
        begin
        while true do
        begin
                if CompareStr(Copy(RecvData, i, 1), FS) = 0 then
                begin
                        j := j + 1;

                        case j of
                                1:
                                        begin
                                        textBox1.Text := copy(RecvData, k, i-k);
                                        end;
                                2:
                                        begin
                                        textBox2.Text := copy(RecvData, k, i-k);
                                        end;
                                3:
                                        begin        
                                        textBox3.Text := copy(RecvData, k, i-k);
                                        end;
                                4:                
                                        begin
                                        textBox4.Text := copy(RecvData, k, i-k);
                                        end;
                                5:
                                        begin
                                        textBox5.Text := copy(RecvData, k, i-k);
                                        end;
                                6:
                                        begin
                                        textBox6.Text := copy(RecvData, k, i-k);
                                        end;
                                7:
                                        begin
                                        textBox7.Text := copy(RecvData, k, i-k);
                                        end;
                                8:
                                        begin
                                        textBox8.Text := copy(RecvData, k, i-k);
                                        EditAgreenum.Text := textBox8.Text;
                                        end;
                                9:
                                        begin
                                        textBox9.Text := copy(RecvData, k, i-k);
                                        end;
                                10:
                                        begin
                                        textBox10.Text := copy(RecvData, k, i-k);
                                        end;
                                11:
                                        begin
                                        textBox11.Text := copy(RecvData, k, i-k);
                                        end;
                                12:
                                        begin
                                        textBox12.Text := copy(RecvData, k, i-k);
                                        end;
                                13:
                                        begin
                                        textBox13.Text := copy(RecvData, k, i-k);
                                        end;
                                14:
                                        begin
                                        textBox14.Text := copy(RecvData, k, i-k);
                                        end;
                                15:
                                        begin
                                        textBox15.Text := copy(RecvData, k, i-k);
                                        end;
                                16:
                                        begin
                                        textBox16.Text := copy(RecvData, k, i-k);
                                        end;
                                17:
                                        begin
                                        textBox17.Text := copy(RecvData, k, i-k);
                                        end;
                                18:
                                        begin
                                        textBox18.Text := copy(RecvData, k, i-k);
                                        end;
                                19:
                                        begin
                                        textBox19.Text := copy(RecvData, k, i-k);
                                        end;
                        end;
                        k := i + 1;

                        if j = 19 then
                        begin
                                break;
                        end;
                end;
                i := i + 1;      
        end;
        end;
end;

procedure TForm1.FormCreate(Sender: TObject);
begin
        ComboHalbu.Items.Add('00');
        ComboHalbu.Items.Add('01');
        ComboHalbu.Items.Add('02');
        ComboHalbu.Items.Add('03');
        ComboHalbu.Items.Add('04');
        ComboHalbu.Items.Add('05');
        ComboHalbu.Items.Add('06');
        ComboHalbu.Items.Add('07');
        ComboHalbu.Items.Add('08');
        ComboHalbu.Items.Add('09');
        ComboHalbu.Items.Add('10');
        ComboHalbu.Items.Add('11');
        ComboHalbu.Items.Add('12');
        ComboHalbu.ItemIndex := 0;

        ComboDeal.Items.Add('신용승인');
        ComboDeal.Items.Add('FALLBACK');
        ComboDeal.Items.Add('신용취소');
        ComboDeal.Items.Add('현금승인');
        ComboDeal.Items.Add('현금취소');
        ComboDeal.Items.Add('은련승인');
        ComboDeal.Items.Add('은련취소');
        ComboDeal.Items.Add('수표조회');
        ComboDeal.Items.Add('현금IC승인');
        ComboDeal.Items.Add('현금IC취소');
        ComboDeal.Items.Add('현금IC승인(멀티패드)');
        ComboDeal.Items.Add('현금IC취소(멀티패드)');
        ComboDeal.Items.Add('그린카드적립승인');
        ComboDeal.Items.Add('그린카드적립취소');
        ComboDeal.Items.Add('DCC환율조회(POS 2TR)');
        ComboDeal.Items.Add('DCC원화통화승인(POS 2TR)');
        ComboDeal.Items.Add('DCC자국통화승인(POS 2TR)');
        ComboDeal.Items.Add('무카드신용부분취소'); //LJY20220224
        ComboDeal.ItemIndex := 0;

        EditAgreedate.Text := FormatDateTime('YYMMDD', now);

        EditAgreenum.Enabled := false;
        EditAgreenum.Color := RGB(124, 124, 124);
        EditAgreedate.Enabled := false;
        EditAgreedate.Color := RGB(124, 124, 124);

        ComboBilltp.Items.Add('00 자기앞수표');
        ComboBilltp.Items.Add('01 가계수표');
        ComboBilltp.Items.Add('02 당좌수표');
        ComboBilltp.ItemIndex := 0;
        
        ComboBillmoney.Items.Add('13 10만원');
        ComboBillmoney.Items.Add('14 30만원');
        ComboBillmoney.Items.Add('15 50만원');
        ComboBillmoney.Items.Add('16 100만원');
        ComboBillmoney.Items.Add('19 비정액');
        ComboBillmoney.ItemIndex := 0;
end;

procedure TForm1.ButtonCnlClick(Sender: TObject);
begin
        ret := mREQ_STOP();
end;          

procedure TForm1.ButtonNICEVCATClick(Sender: TObject);
var
        RecvBuf : PChar;
begin
        RecvBuf := Nil;
        RecvBuf := AllocMem(2480);

        FS := char($1C);
        ret := mNICEVCAT(EditSend.Text, RecvBuf);
        ShowMessage('ret : ' + IntToStr(ret)); //리턴값 처리 꼭 해주세요.

        if ret <> 1 then
                begin
                        Exit;
                        //Form1.Close;
                end;

        EditRecv.Text := StrPas(RecvBuf);
end;

procedure TForm1.ButtonResetClick(Sender: TObject);
begin
        ret := mREADER_RESET(EditWaittime.Text);
end;

procedure TForm1.ButtonRestartClick(Sender: TObject);
begin
        ret := mRESTART();                  
end;

procedure TForm1.ComboDealSelect(Sender: TObject);
begin
        case comboDeal.ItemIndex of
        0, 1, 3, 5, 8, 10, 12:
                begin
                        EditAgreenum.Enabled := false;
                        EditAgreenum.Color := RGB(124, 124, 124);
                        EditAgreedate.Enabled := false;
                        EditAgreedate.Color := RGB(124, 124, 124);
                end;
        2, 4, 6, 9, 11, 13:
                begin
                        EditAgreenum.Enabled := true;
                        EditAgreenum.Color := RGB(255, 255, 255);
                        EditAgreedate.Enabled := true;
                        EditAgreedate.Color := RGB(255, 255, 255);
                end;
        end;

        case comboDeal.ItemIndex of
        0, 1, 2, 5, 6:              
                begin
                Label2.Caption := '할부';
                ComboHalbu.Items.Clear;
                ComboHalbu.Items.Add('00');
                ComboHalbu.Items.Add('01');
                ComboHalbu.Items.Add('02');
                ComboHalbu.Items.Add('03');
                ComboHalbu.Items.Add('04');
                ComboHalbu.Items.Add('05');
                ComboHalbu.Items.Add('06');
                ComboHalbu.Items.Add('07');
                ComboHalbu.Items.Add('08');
                ComboHalbu.Items.Add('09');   
                ComboHalbu.Items.Add('10');
                ComboHalbu.Items.Add('11');
                ComboHalbu.Items.Add('12');
                ComboHalbu.ItemIndex := 0;
                end;
        3, 4:
                begin
                Label2.Caption := '발급구분';
                ComboHalbu.Items.Clear;
                ComboHalbu.Items.Add('01소비자');
                ComboHalbu.Items.Add('02사업자');
                ComboHalbu.Items.Add('03자진발급');
                ComboHalbu.ItemIndex := 0;
                end; 
        end;
end;

procedure TForm1.Button1Click(Sender: TObject);
begin
        ret := mCHK_CASHIC_MP();
        //0이상 : 연결된 계좌수
        //-1 : 현금IC 카드 아님
        //-2 : 리더기 PORT OPEN 오류
        //-3 : 카드리딩 타임아웃
        //-4 : 사용자 및 리더기 리딩 요청 취소
        //-5 : 응답데이터가 없거나 응답데이터 오류
        //-9 : 기타오류
        //-17 : NVCAT 중복요청 오류
        ShowMessage(IntToStr(ret));
end;

procedure TForm1.Button2Click(Sender: TObject);
var
        RecvBuf : PChar;
begin
        RecvBuf := Nil;
        RecvBuf := AllocMem(2480);
        
        ret := mCHK_CARDIN_MP(RecvBuf);
        //1 : 정상
        //-11 : 카드리더 PORT OPEN 오류
        //-3 : 연결된 장비 응답 없음
        //-1 : 응답데이터 수신 실패
        //-8 : 해당 기능 미지원 장비
        ShowMessage(IntToStr(ret));

        if ret <> 1 then
                begin
                        Exit;
                end;
        
        ShowMessage('응답데이터 : ' + StrPas(RecvBuf));
end;

procedure TForm1.Button3Click(Sender: TObject);
var
        RecvBuf : PChar;
begin
        RecvBuf := Nil;
        RecvBuf := AllocMem(2480);
        
        ret := mREQ_BARCODE('1', RecvBuf);
        ShowMessage(IntToStr(ret));

        if ret <> 1 then
                begin
                        Exit;
                end;
        
        ShowMessage('응답데이터 : ' + StrPas(RecvBuf));
end;

procedure TForm1.Button4Click(Sender: TObject);
begin
        ret := mCHK_CASHIC2();
        ShowMessage(IntToStr(ret));
end;

procedure TForm1.Button5Click(Sender: TObject);
begin
        ret := mNVCATSHUTDOWN();
end;

procedure TForm1.Button6Click(Sender: TObject);
var
        NiceDownYN, CustomCnl : String;
begin
        ShowMessage('가맹점다운로드 테스트시 T / 운영시 1(Default)');
        ShowMessage('부정취소 미사용시 Y / 사용시 N(Default)');
        ret := mSetCnlDisableYN(EditNiceDownYN.Text, EditCustomCnl.Text);
        ShowMessage(IntToStr(ret));
end;

procedure TForm1.Button7Click(Sender: TObject);
var
        MAC : PChar;
begin
        MAC := Nil;
        MAC := AllocMem(2480);
        
        ret := mGetMac(MAC);
        ShowMessage(IntToStr(ret));

        if ret <> 1 then
                begin
                        Exit;
                end;
        
        ShowMessage('MAC : ' + StrPas(MAC));
end;

procedure TForm1.Button8Click(Sender: TObject);
begin
        ret := mREQ_TITLOCK();
        ShowMessage(IntToStr(ret));
end;

end.
