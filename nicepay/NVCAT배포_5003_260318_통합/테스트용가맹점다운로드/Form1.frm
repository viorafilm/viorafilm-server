VERSION 5.00
Begin VB.Form Form1 
   Caption         =   "NicePosICV105 TEST"
   ClientHeight    =   4335
   ClientLeft      =   120
   ClientTop       =   450
   ClientWidth     =   7005
   BeginProperty Font 
      Name            =   "맑은 고딕"
      Size            =   12
      Charset         =   129
      Weight          =   700
      Underline       =   0   'False
      Italic          =   0   'False
      Strikethrough   =   0   'False
   EndProperty
   LinkTopic       =   "Form1"
   ScaleHeight     =   4335
   ScaleWidth      =   7005
   StartUpPosition =   3  'Windows 기본값
   Begin VB.CommandButton Command11 
      Caption         =   "가맹점 다운로드 테스트"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   9.75
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   495
      Left            =   3600
      TabIndex        =   16
      Top             =   1800
      Width           =   3015
   End
   Begin VB.CommandButton Command16 
      Caption         =   "갱신키 다운로드"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   9.75
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   495
      Left            =   3600
      TabIndex        =   14
      Top             =   3600
      Width           =   3015
   End
   Begin VB.TextBox DownRecv 
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   9.75
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   495
      Left            =   1680
      TabIndex        =   13
      Top             =   2400
      Width           =   4935
   End
   Begin VB.CommandButton Command6 
      Caption         =   "최초키 다운로드"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   9.75
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   495
      Left            =   360
      TabIndex        =   12
      Top             =   3600
      Width           =   3015
   End
   Begin VB.CommandButton Command5 
      Caption         =   "상호인증 및 무결성점검"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   9.75
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   495
      Left            =   360
      TabIndex        =   11
      Top             =   3000
      Width           =   3015
   End
   Begin VB.CommandButton Command3 
      Caption         =   "가맹점 다운로드 리얼 "
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   9.75
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   495
      Left            =   360
      TabIndex        =   10
      Top             =   1800
      Width           =   3015
   End
   Begin VB.CommandButton Command2 
      Caption         =   "환경설정 가져오기 (GetEnv)"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   9.75
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   495
      Left            =   360
      TabIndex        =   9
      Top             =   1200
      Visible         =   0   'False
      Width           =   3015
   End
   Begin VB.CommandButton Command1 
      Caption         =   "환경설정 (SetEnv)"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   9.75
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   495
      Left            =   3600
      TabIndex        =   8
      Top             =   1200
      Visible         =   0   'False
      Width           =   3015
   End
   Begin VB.TextBox BizNum 
      Alignment       =   2  '가운데 맞춤
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   9.75
         Charset         =   129
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   375
      Left            =   4920
      TabIndex        =   7
      Text            =   "2208115770"
      Top             =   720
      Width           =   1695
   End
   Begin VB.TextBox CatId 
      Alignment       =   2  '가운데 맞춤
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   9.75
         Charset         =   129
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   375
      Left            =   4920
      TabIndex        =   6
      Text            =   "2393300001"
      Top             =   240
      Width           =   1695
   End
   Begin VB.TextBox Baud 
      Alignment       =   2  '가운데 맞춤
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   9.75
         Charset         =   129
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   375
      Left            =   1680
      TabIndex        =   5
      Text            =   "115200"
      Top             =   720
      Width           =   1695
   End
   Begin VB.TextBox Port 
      Alignment       =   2  '가운데 맞춤
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   9.75
         Charset         =   129
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   375
      Left            =   1680
      TabIndex        =   4
      Text            =   "1"
      Top             =   240
      Width           =   1695
   End
   Begin VB.Label Label7 
      AutoSize        =   -1  'True
      Caption         =   "DownRecv"
      Height          =   315
      Left            =   360
      TabIndex        =   15
      Top             =   2520
      Width           =   1215
   End
   Begin VB.Label Label4 
      AutoSize        =   -1  'True
      Caption         =   "사업자번호"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   11.25
         Charset         =   129
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   300
      Left            =   3600
      TabIndex        =   3
      Top             =   720
      Width           =   1125
   End
   Begin VB.Label Label3 
      AutoSize        =   -1  'True
      Caption         =   "CATID"
      Height          =   315
      Left            =   3600
      TabIndex        =   2
      Top             =   240
      Width           =   705
   End
   Begin VB.Label Label2 
      AutoSize        =   -1  'True
      Caption         =   "리더 Baud"
      Height          =   315
      Left            =   360
      TabIndex        =   1
      Top             =   720
      Width           =   1155
   End
   Begin VB.Label Label1 
      AutoSize        =   -1  'True
      Caption         =   "리더 Port"
      Height          =   315
      Left            =   360
      TabIndex        =   0
      Top             =   240
      Width           =   1050
   End
End
Attribute VB_Name = "Form1"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Option Explicit

Private Declare Function SetEnv Lib "NICEPOSICV105.dll" (ByVal RPort As String, ByVal RBaud As String, ByVal BizNo As String, ByVal CatId As String, ByVal SUse As String, ByVal SPorta As String, ByVal SBaud As String) As Long
Private Declare Function GetEnv Lib "NICEPOSICV105.dll" (ByRef RPort As Byte, ByRef RBaud As Byte, ByRef BizNo As Byte, ByRef CatId As Byte, ByRef SUse As Byte, ByRef SPorta As Byte, ByRef SBaud As Byte) As Long
Private Declare Function NICEDOWN Lib "NICEPOSICV105.dll" (ByVal dn_tp As String, ByVal ins_hw As String, ByRef recv_data As Byte) As Long '다운로드유형, 설치 단말기 정보, 응답전문
Private Declare Function ChkValid Lib "NICEPOSICV105.dll" (ByRef errcode As Byte) As Long
Private Declare Function EncKeyDown Lib "NICEPOSICV105.dll" (ByVal flag As String) As Long
Private Declare Function OpenPort Lib "NICEPOSICV105.dll" (ByVal iPort As Long, ByVal iBaud As Long) As Long
Private Declare Function ClosePort Lib "NICEPOSICV105.dll" () As Long

Dim CardRead As Integer
Dim FBTemp As String
Dim AgrNumTemp As String
Dim AgrDateTemp As String
Dim fallback As String

Private Sub Command1_Click() '가맹점 정보 등록
    Dim ret As Long
    ret = SetEnv(Port.Text, Baud.Text, BizNum.Text, CatId.Text, "", "", "")
    
    If ret = 1 Then
        MsgBox ("성공")
    Else
        MsgBox ("실패!")
    End If
End Sub



Public Function HMid(myString As String, intStr As Integer, intLen As Integer) As String
    '한글포함된 문장에서 Mid 함수 쓰기
    HMid = StrConv(MidB(StrConv(myString, vbFromUnicode), intStr, intLen), vbUnicode)
End Function

Private Sub Command11_Click()
    Dim ret As Long
    
    Dim mDn_Tp As String
    Dim mIns_Hw As String
    Dim mRecv_Data(2000) As Byte
    
    mDn_Tp = "T" '운영 : 1, 테스트 : T
    mIns_Hw = ""
    
    ret = NICEDOWN(mDn_Tp, mIns_Hw, mRecv_Data(0))
    If ret = 1 Then
        DownRecv.Text = StrConv(mRecv_Data, vbUnicode)
    Else
        MsgBox ("실패")
    End If
End Sub

Private Sub Command16_Click()
    Dim ret As Long
    
    Dim mFlag As String
    mFlag = "2"
    
    ret = EncKeyDown(mFlag)
    If ret = 1 Then
        MsgBox ("성공")
    Else
        MsgBox ("실패!")
    End If
End Sub



Private Sub Command2_Click() '환경설정 가져오기
    Dim ret As Long
    
    Dim mPort(100) As Byte
    Dim mBaud(100) As Byte
    Dim mBizNum(100) As Byte
    Dim mCatId(100) As Byte
    Dim mSUse(100) As Byte
    Dim mSPort(100) As Byte
    Dim mSBaud(100) As Byte
    ret = GetEnv(mPort(0), mBaud(0), mBizNum(0), mCatId(0), mSUse(0), mSPort(0), mSBaud(0))
    
    If ret = 1 Then
        Port.Text = StrConv(mPort, vbUnicode)
        Baud.Text = StrConv(mBaud, vbUnicode)
        BizNum.Text = StrConv(mBizNum, vbUnicode)
        CatId.Text = StrConv(mCatId, vbUnicode)
    Else
        MsgBox ("GetStrEnv 실패!")
    End If
End Sub



Private Sub Command3_Click() '가맹점 다운로드
    Dim ret As Long
    
    Dim mDn_Tp As String
    Dim mIns_Hw As String
    Dim mRecv_Data(2000) As Byte
    
    mDn_Tp = "1" '운영 : 1, 테스트 : T
    mIns_Hw = ""
    
    ret = NICEDOWN(mDn_Tp, mIns_Hw, mRecv_Data(0))
    If ret = 1 Then
        DownRecv.Text = StrConv(mRecv_Data, vbUnicode)
    Else
        MsgBox ("실패")
    End If
End Sub
Private Sub Command5_Click()
    Dim ret As Long
    
    Dim mErrCode(100) As Byte
    ret = ChkValid(mErrCode(0))
    If ret = 1 Then
        MsgBox ("성공")
        MsgBox (StrConv(mErrCode, vbUnicode))
    Else
        MsgBox ("실패")
        MsgBox (StrConv(mErrCode, vbUnicode))
    End If
End Sub

Private Sub Command6_Click()
    Dim ret As Long
    
    Dim mFlag As String
    mFlag = "1"
    
    ret = EncKeyDown(mFlag)
    If ret = 1 Then
        MsgBox ("성공")
    Else
        MsgBox ("실패!")
    End If
End Sub
Private Sub Form_Load()
    Call Command2_Click
End Sub

Private Sub Form_Unload(Cancel As Integer)
    Dim ret As Long
    
    ret = ClosePort()
End Sub

