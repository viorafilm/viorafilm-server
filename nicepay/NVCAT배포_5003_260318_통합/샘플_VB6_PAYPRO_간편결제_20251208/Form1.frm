VERSION 5.00
Begin VB.Form Form1 
   Caption         =   "NVCAT 바코드테스트"
   ClientHeight    =   8235
   ClientLeft      =   120
   ClientTop       =   465
   ClientWidth     =   12735
   LinkTopic       =   "Form1"
   ScaleHeight     =   8235
   ScaleWidth      =   12735
   Begin VB.TextBox ApprPersonno 
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   6000
      TabIndex        =   136
      Top             =   2400
      Width           =   615
   End
   Begin VB.CommandButton Command38 
      Caption         =   "페이코취소"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   4680
      TabIndex        =   135
      Top             =   7800
      Width           =   1935
   End
   Begin VB.CommandButton Command37 
      Caption         =   "페이코승인"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   2520
      TabIndex        =   134
      Top             =   7800
      Width           =   1935
   End
   Begin VB.TextBox MPAddInfoYN 
      BeginProperty Font 
         Name            =   "굴림"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   312
      Left            =   7920
      TabIndex        =   128
      Top             =   5640
      Width           =   495
   End
   Begin VB.TextBox MPBizCode 
      BeginProperty Font 
         Name            =   "굴림"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   312
      Left            =   9600
      TabIndex        =   127
      Top             =   5640
      Width           =   615
   End
   Begin VB.TextBox MPAddInfo 
      BeginProperty Font 
         Name            =   "굴림"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   312
      Left            =   7920
      TabIndex        =   126
      Top             =   6000
      Width           =   4575
   End
   Begin VB.TextBox MPFiller2 
      BeginProperty Font 
         Name            =   "굴림"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   312
      Left            =   7920
      TabIndex        =   125
      Top             =   6360
      Width           =   4575
   End
   Begin VB.CommandButton Command36 
      Caption         =   "PASS 주민번호"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   5160
      TabIndex        =   124
      Top             =   6720
      Width           =   1455
   End
   Begin VB.CommandButton Command35 
      Caption         =   "PASS 운전면허"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   3600
      TabIndex        =   123
      Top             =   6720
      Width           =   1455
   End
   Begin VB.CommandButton Command34 
      Caption         =   "Req_Barcode"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   1440
      TabIndex        =   122
      Top             =   840
      Width           =   1455
   End
   Begin VB.CommandButton Command22 
      Caption         =   "서명요청 취소"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   4800
      TabIndex        =   121
      Top             =   840
      Width           =   1815
   End
   Begin VB.TextBox Text31 
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   9600
      TabIndex        =   119
      Top             =   4440
      Width           =   2895
   End
   Begin VB.TextBox Text30 
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   7680
      TabIndex        =   117
      Top             =   4440
      Width           =   1215
   End
   Begin VB.TextBox Text29 
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   10920
      TabIndex        =   115
      Top             =   4080
      Width           =   1575
   End
   Begin VB.TextBox Text28 
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   8880
      TabIndex        =   113
      Top             =   4080
      Width           =   855
   End
   Begin VB.TextBox ApprDealno 
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   1440
      TabIndex        =   111
      Top             =   2400
      Width           =   1455
   End
   Begin VB.TextBox ApprFiller 
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   3480
      TabIndex        =   110
      Top             =   2400
      Width           =   1215
   End
   Begin VB.CommandButton Command33 
      Caption         =   "카카오취소인증(2TR)"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   360
      TabIndex        =   108
      Top             =   7440
      Width           =   1935
   End
   Begin VB.TextBox Text27 
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   11880
      TabIndex        =   106
      Top             =   3720
      Width           =   615
   End
   Begin VB.TextBox Text26 
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   9720
      TabIndex        =   104
      Top             =   3720
      Width           =   1215
   End
   Begin VB.TextBox Text25 
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   11040
      TabIndex        =   102
      Top             =   3360
      Width           =   1455
   End
   Begin VB.TextBox Text24 
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   11280
      TabIndex        =   100
      Top             =   3000
      Width           =   1215
   End
   Begin VB.TextBox Text23 
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   9240
      TabIndex        =   98
      Top             =   3000
      Width           =   1215
   End
   Begin VB.TextBox Text22 
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   7320
      TabIndex        =   96
      Top             =   3000
      Width           =   1215
   End
   Begin VB.TextBox Text21 
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   10800
      TabIndex        =   94
      Top             =   2640
      Width           =   1695
   End
   Begin VB.TextBox Text20 
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   7800
      TabIndex        =   92
      Top             =   2640
      Width           =   1695
   End
   Begin VB.TextBox Text19 
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   12240
      TabIndex        =   90
      Top             =   2280
      Width           =   255
   End
   Begin VB.TextBox Text18 
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   7440
      TabIndex        =   88
      Top             =   2280
      Width           =   3975
   End
   Begin VB.TextBox Text17 
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   11040
      TabIndex        =   86
      Top             =   1920
      Width           =   1455
   End
   Begin VB.TextBox Text16 
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   9120
      TabIndex        =   84
      Top             =   1920
      Width           =   975
   End
   Begin VB.TextBox Text15 
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   7560
      TabIndex        =   82
      Top             =   1920
      Width           =   975
   End
   Begin VB.TextBox Text14 
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   10440
      TabIndex        =   80
      Top             =   1560
      Width           =   2055
   End
   Begin VB.TextBox Text13 
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   8760
      TabIndex        =   78
      Top             =   1560
      Width           =   615
   End
   Begin VB.TextBox Text12 
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   7560
      TabIndex        =   76
      Top             =   1560
      Width           =   375
   End
   Begin VB.TextBox Text11 
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   11880
      TabIndex        =   74
      Top             =   1200
      Width           =   615
   End
   Begin VB.TextBox Text10 
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   10680
      TabIndex        =   72
      Top             =   1200
      Width           =   375
   End
   Begin VB.TextBox Text9 
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   9120
      TabIndex        =   70
      Top             =   1200
      Width           =   615
   End
   Begin VB.TextBox Text8 
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   7440
      TabIndex        =   68
      Top             =   1200
      Width           =   855
   End
   Begin VB.TextBox Text7 
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   12120
      TabIndex        =   66
      Top             =   840
      Width           =   375
   End
   Begin VB.TextBox Text6 
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   10680
      TabIndex        =   64
      Top             =   840
      Width           =   975
   End
   Begin VB.TextBox Text5 
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   8040
      TabIndex        =   62
      Top             =   840
      Width           =   975
   End
   Begin VB.TextBox Text4 
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   11280
      TabIndex        =   60
      Top             =   480
      Width           =   1215
   End
   Begin VB.TextBox Text3 
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   9960
      TabIndex        =   58
      Top             =   480
      Width           =   495
   End
   Begin VB.TextBox Text2 
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   8760
      TabIndex        =   56
      Top             =   480
      Width           =   375
   End
   Begin VB.TextBox Text1 
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   7440
      TabIndex        =   54
      Top             =   480
      Width           =   495
   End
   Begin VB.CommandButton Command32 
      Caption         =   "카카오머니취소"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   4680
      TabIndex        =   52
      Top             =   7080
      Width           =   1935
   End
   Begin VB.CommandButton Command31 
      Caption         =   "카카오카드취소"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   4680
      TabIndex        =   51
      Top             =   7440
      Width           =   1935
   End
   Begin VB.CommandButton Command30 
      Caption         =   "카카오카드승인"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   2520
      TabIndex        =   50
      Top             =   7440
      Width           =   1935
   End
   Begin VB.CommandButton Command29 
      Caption         =   "카카오머니승인"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   2520
      TabIndex        =   49
      Top             =   7080
      Width           =   1935
   End
   Begin VB.CommandButton Command28 
      Caption         =   "카카오승인인증(2TR)"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   360
      TabIndex        =   48
      Top             =   7080
      Width           =   1935
   End
   Begin VB.CommandButton Command27 
      Caption         =   "앱카드취소"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   1920
      TabIndex        =   47
      Top             =   6720
      Width           =   1455
   End
   Begin VB.CommandButton Command26 
      Caption         =   "앱카드승인"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   360
      TabIndex        =   46
      Top             =   6720
      Width           =   1455
   End
   Begin VB.TextBox Textno 
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   1440
      TabIndex        =   43
      Top             =   2040
      Width           =   1455
   End
   Begin VB.TextBox Money 
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   1440
      TabIndex        =   40
      Text            =   "1004"
      Top             =   1680
      Width           =   975
   End
   Begin VB.CommandButton Command25 
      Caption         =   "알리페이/위챗페이/카카오페이/SSGPAY/LPAY/제로페이/BCQR 승인 (PAYPRO통합)"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   360
      TabIndex        =   39
      Top             =   3600
      Width           =   6255
   End
   Begin VB.CommandButton Command24 
      Caption         =   "알리페이/위챗페이/카카오페이/SSGPAY/LPAY/제로페이/BCQR 취소 (PAYPRO통합)"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   360
      TabIndex        =   38
      Top             =   3960
      Width           =   6255
   End
   Begin VB.CommandButton Command23 
      Caption         =   "IP/PORT 설정"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   9
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   5040
      TabIndex        =   37
      Top             =   3120
      Width           =   1575
   End
   Begin VB.TextBox ServerIp 
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   9
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   1440
      TabIndex        =   34
      Text            =   "10.222.141.100"
      Top             =   3120
      Width           =   1455
   End
   Begin VB.TextBox ServerPort 
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   9
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   4200
      TabIndex        =   33
      Text            =   "47520"
      Top             =   3120
      Width           =   615
   End
   Begin VB.TextBox SignData 
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   9
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   1440
      TabIndex        =   31
      Top             =   2760
      Width           =   5175
   End
   Begin VB.CommandButton Command21 
      Caption         =   "BC/은련QR취소"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   1920
      TabIndex        =   30
      Top             =   4920
      Width           =   1455
   End
   Begin VB.CommandButton Command20 
      Caption         =   "BC/은련QR승인"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   360
      TabIndex        =   29
      Top             =   4920
      Width           =   1455
   End
   Begin VB.CommandButton Command19 
      Caption         =   "알리페이승인"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   3600
      TabIndex        =   28
      Top             =   6000
      Width           =   1455
   End
   Begin VB.CommandButton Command18 
      Caption         =   "알리페이취소"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   5160
      TabIndex        =   27
      Top             =   6000
      Width           =   1455
   End
   Begin VB.CommandButton Command17 
      Caption         =   "위챗페이취소"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   1920
      TabIndex        =   26
      Top             =   6000
      Width           =   1455
   End
   Begin VB.CommandButton Command16 
      Caption         =   "위챗페이승인"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   360
      TabIndex        =   25
      Top             =   6000
      Width           =   1455
   End
   Begin VB.CommandButton Command15 
      Caption         =   "캐시백취소"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   5160
      TabIndex        =   24
      Top             =   5640
      Width           =   1455
   End
   Begin VB.CommandButton Command14 
      Caption         =   "캐시백승인"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   3600
      TabIndex        =   23
      Top             =   5640
      Width           =   1455
   End
   Begin VB.CommandButton Command13 
      Caption         =   "KT취소"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   1920
      TabIndex        =   22
      Top             =   5640
      Width           =   1455
   End
   Begin VB.CommandButton Command12 
      Caption         =   "KT승인"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   360
      TabIndex        =   21
      Top             =   5640
      Width           =   1455
   End
   Begin VB.CommandButton Command11 
      Caption         =   "SKT승인"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   360
      TabIndex        =   20
      Top             =   5280
      Width           =   1455
   End
   Begin VB.CommandButton Command10 
      Caption         =   "SKT취소"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   1920
      TabIndex        =   19
      Top             =   5280
      Width           =   1455
   End
   Begin VB.CommandButton Command9 
      Caption         =   "유플러스취소"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   5160
      TabIndex        =   18
      Top             =   5280
      Width           =   1455
   End
   Begin VB.CommandButton Command8 
      Caption         =   "유플러스승인"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   3600
      TabIndex        =   17
      Top             =   5280
      Width           =   1455
   End
   Begin VB.CommandButton Command7 
      Caption         =   "현금영수증취소"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   5160
      TabIndex        =   16
      Top             =   4920
      Width           =   1455
   End
   Begin VB.CommandButton Command6 
      Caption         =   "현금영수증승인"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   3600
      TabIndex        =   15
      Top             =   4920
      Width           =   1455
   End
   Begin VB.CommandButton Command5 
      Caption         =   "카카오페이취소"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   5160
      TabIndex        =   14
      Top             =   6360
      Width           =   1455
   End
   Begin VB.CommandButton Command4 
      Caption         =   "카카오페이승인"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   3600
      TabIndex        =   13
      Top             =   6360
      Width           =   1455
   End
   Begin VB.TextBox Apprdate 
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   5760
      TabIndex        =   11
      Top             =   1680
      Width           =   855
   End
   Begin VB.TextBox Apprno 
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   3360
      TabIndex        =   9
      Top             =   1680
      Width           =   1335
   End
   Begin VB.CommandButton Command3 
      Caption         =   "제로페이취소"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   1920
      TabIndex        =   8
      Top             =   6360
      Width           =   1455
   End
   Begin VB.CommandButton Command2 
      Caption         =   "제로페이승인"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   360
      TabIndex        =   7
      Top             =   6360
      Width           =   1455
   End
   Begin VB.TextBox Barcode 
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   1440
      TabIndex        =   5
      Top             =   1320
      Width           =   5175
   End
   Begin VB.TextBox SendData 
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   1440
      TabIndex        =   2
      Top             =   120
      Width           =   5175
   End
   Begin VB.TextBox RecvData 
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   1440
      TabIndex        =   1
      Top             =   480
      Width           =   5175
   End
   Begin VB.CommandButton Command1 
      Caption         =   "NICEVCATB"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   330
      Left            =   3000
      TabIndex        =   0
      Top             =   840
      Width           =   1695
   End
   Begin VB.Label Label13 
      AutoSize        =   -1  'True
      Caption         =   "서명표시금액"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   9
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   225
      Left            =   4800
      TabIndex        =   137
      Top             =   2415
      Width           =   1080
   End
   Begin VB.Label Label12 
      AutoSize        =   -1  'True
      Caption         =   "머니플러스 사용 시 아래 정보 입력 후 거래 요청"
      BeginProperty Font 
         Name            =   "굴림"
         Size            =   8.25
         Charset         =   129
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   165
      Left            =   6840
      TabIndex        =   133
      Top             =   5400
      Width           =   4020
   End
   Begin VB.Label Label63 
      AutoSize        =   -1  'True
      Caption         =   "가맹점코드"
      BeginProperty Font 
         Name            =   "굴림"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   165
      Left            =   8640
      TabIndex        =   132
      Top             =   5760
      Width           =   825
   End
   Begin VB.Label Label62 
      AutoSize        =   -1  'True
      Caption         =   "부가정보여부"
      BeginProperty Font 
         Name            =   "굴림"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   165
      Left            =   6840
      TabIndex        =   131
      Top             =   5760
      Width           =   990
   End
   Begin VB.Label Label64 
      AutoSize        =   -1  'True
      Caption         =   "부가정보"
      BeginProperty Font 
         Name            =   "굴림"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   165
      Left            =   6840
      TabIndex        =   130
      Top             =   6120
      Width           =   660
   End
   Begin VB.Label Label65 
      AutoSize        =   -1  'True
      Caption         =   "Filler2"
      BeginProperty Font 
         Name            =   "굴림"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   165
      Left            =   6840
      TabIndex        =   129
      Top             =   6480
      Width           =   495
   End
   Begin VB.Label Label48 
      AutoSize        =   -1  'True
      Caption         =   "Filler"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   195
      Left            =   9120
      TabIndex        =   120
      Top             =   4485
      Width           =   360
   End
   Begin VB.Label Label47 
      AutoSize        =   -1  'True
      Caption         =   "실승인금액"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   195
      Left            =   6720
      TabIndex        =   118
      Top             =   4452
      Width           =   825
   End
   Begin VB.Label Label46 
      AutoSize        =   -1  'True
      Caption         =   "거래고유번호"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   195
      Left            =   9840
      TabIndex        =   116
      Top             =   4125
      Width           =   990
   End
   Begin VB.Label Label45 
      AutoSize        =   -1  'True
      Caption         =   "CAT단말기 취소용 승인번호"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   195
      Left            =   6720
      TabIndex        =   114
      Top             =   4125
      Width           =   2070
   End
   Begin VB.Label Label44 
      AutoSize        =   -1  'True
      Caption         =   "원거래고유번호"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   9
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   225
      Left            =   120
      TabIndex        =   112
      Top             =   2400
      Width           =   1260
   End
   Begin VB.Label Label43 
      AutoSize        =   -1  'True
      Caption         =   "Filler"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   9
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   225
      Left            =   3000
      TabIndex        =   109
      Top             =   2400
      Width           =   375
   End
   Begin VB.Label Label42 
      AutoSize        =   -1  'True
      Caption         =   "기기번호"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   195
      Left            =   11160
      TabIndex        =   107
      Top             =   3765
      Width           =   660
   End
   Begin VB.Label Label41 
      AutoSize        =   -1  'True
      Caption         =   "캐시백승인번호/UPLAN쿠폰코드(Filler)"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   195
      Left            =   6720
      TabIndex        =   105
      Top             =   3765
      Width           =   2835
   End
   Begin VB.Label Label40 
      AutoSize        =   -1  'True
      Caption         =   "캐시백가맹점/TLV포멧/카카오거래구분자(신판실승인금액)"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   195
      Left            =   6720
      TabIndex        =   103
      Top             =   3405
      Width           =   4275
   End
   Begin VB.Label Label39 
      AutoSize        =   -1  'True
      Caption         =   "누적P"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   195
      Left            =   10680
      TabIndex        =   101
      Top             =   3045
      Width           =   420
   End
   Begin VB.Label Label38 
      AutoSize        =   -1  'True
      Caption         =   "가용P"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   195
      Left            =   8640
      TabIndex        =   99
      Top             =   3045
      Width           =   420
   End
   Begin VB.Label Label37 
      AutoSize        =   -1  'True
      Caption         =   "발생P"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   195
      Left            =   6720
      TabIndex        =   97
      Top             =   3045
      Width           =   420
   End
   Begin VB.Label Label36 
      AutoSize        =   -1  'True
      Caption         =   "거래일련번호"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   195
      Left            =   9720
      TabIndex        =   95
      Top             =   2685
      Width           =   990
   End
   Begin VB.Label Label35 
      AutoSize        =   -1  'True
      Caption         =   "전문관리번호"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   195
      Left            =   6720
      TabIndex        =   93
      Top             =   2685
      Width           =   990
   End
   Begin VB.Label Label34 
      AutoSize        =   -1  'True
      Caption         =   "카드구분"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   195
      Left            =   11520
      TabIndex        =   91
      Top             =   2325
      Width           =   660
   End
   Begin VB.Label Label33 
      AutoSize        =   -1  'True
      Caption         =   "카드BIN"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   195
      Left            =   6720
      TabIndex        =   89
      Top             =   2325
      Width           =   585
   End
   Begin VB.Label Label32 
      AutoSize        =   -1  'True
      Caption         =   "응답메세지"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   195
      Left            =   10200
      TabIndex        =   87
      Top             =   1965
      Width           =   825
   End
   Begin VB.Label Label31 
      AutoSize        =   -1  'True
      Caption         =   "잔액"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   195
      Left            =   8640
      TabIndex        =   85
      Top             =   1965
      Width           =   330
   End
   Begin VB.Label Label30 
      AutoSize        =   -1  'True
      Caption         =   "승인CATID"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   195
      Left            =   6720
      TabIndex        =   83
      Top             =   1965
      Width           =   795
   End
   Begin VB.Label Label29 
      AutoSize        =   -1  'True
      Caption         =   "가맹점번호"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   195
      Left            =   9480
      TabIndex        =   81
      Top             =   1605
      Width           =   825
   End
   Begin VB.Label Label28 
      AutoSize        =   -1  'True
      Caption         =   "매입사명"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   195
      Left            =   8040
      TabIndex        =   79
      Top             =   1605
      Width           =   660
   End
   Begin VB.Label Label27 
      AutoSize        =   -1  'True
      Caption         =   "매입사코드"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   195
      Left            =   6720
      TabIndex        =   77
      Top             =   1605
      Width           =   825
   End
   Begin VB.Label Label26 
      AutoSize        =   -1  'True
      Caption         =   "발급사명"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   195
      Left            =   11160
      TabIndex        =   75
      Top             =   1245
      Width           =   660
   End
   Begin VB.Label Label25 
      AutoSize        =   -1  'True
      Caption         =   "발급사코드"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   195
      Left            =   9840
      TabIndex        =   73
      Top             =   1245
      Width           =   825
   End
   Begin VB.Label Label24 
      AutoSize        =   -1  'True
      Caption         =   "승인일시"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   195
      Left            =   8400
      TabIndex        =   71
      Top             =   1245
      Width           =   660
   End
   Begin VB.Label Label23 
      AutoSize        =   -1  'True
      Caption         =   "승인번호"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   195
      Left            =   6720
      TabIndex        =   69
      Top             =   1245
      Width           =   660
   End
   Begin VB.Label Label22 
      AutoSize        =   -1  'True
      Caption         =   "할부"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   195
      Left            =   11760
      TabIndex        =   67
      Top             =   885
      Width           =   330
   End
   Begin VB.Label Label21 
      AutoSize        =   -1  'True
      Caption         =   "봉사료(포인트구분)"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   195
      Left            =   9120
      TabIndex        =   65
      Top             =   885
      Width           =   1410
   End
   Begin VB.Label Label20 
      AutoSize        =   -1  'True
      Caption         =   "부가세(적립구분)"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   195
      Left            =   6720
      TabIndex        =   63
      Top             =   885
      Width           =   1245
   End
   Begin VB.Label Label19 
      AutoSize        =   -1  'True
      Caption         =   "거래금액"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   195
      Left            =   10560
      TabIndex        =   61
      Top             =   525
      Width           =   660
   End
   Begin VB.Label Label18 
      AutoSize        =   -1  'True
      Caption         =   "응답코드"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   195
      Left            =   9240
      TabIndex        =   59
      Top             =   525
      Width           =   660
   End
   Begin VB.Label Label17 
      AutoSize        =   -1  'True
      Caption         =   "거래유형"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   195
      Left            =   8040
      TabIndex        =   57
      Top             =   525
      Width           =   660
   End
   Begin VB.Label Label16 
      AutoSize        =   -1  'True
      Caption         =   "거래구분"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   195
      Left            =   6720
      TabIndex        =   55
      Top             =   525
      Width           =   660
   End
   Begin VB.Label Label15 
      AutoSize        =   -1  'True
      Caption         =   "응답전문 Parsing"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   9
         Charset         =   129
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   225
      Left            =   6720
      TabIndex        =   53
      Top             =   120
      Width           =   1425
   End
   Begin VB.Label Label14 
      AutoSize        =   -1  'True
      Caption         =   "알리(23)/위챗(20)+""01""+yyMMddHHmmss+Rnd(4)"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   195
      Left            =   3000
      TabIndex        =   45
      Top             =   2085
      Width           =   3750
   End
   Begin VB.Label Label11 
      AutoSize        =   -1  'True
      Caption         =   "전문관리번호"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   9
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   225
      Left            =   240
      TabIndex        =   44
      Top             =   2055
      Width           =   1080
   End
   Begin VB.Label Label10 
      AutoSize        =   -1  'True
      Caption         =   "PAYPRO 통합전문이 아닌 별도 전문 사용시 아래 예제 참고하시길 바랍니다."
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   9
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   225
      Left            =   360
      TabIndex        =   42
      Top             =   4560
      Width           =   6120
   End
   Begin VB.Line Line1 
      X1              =   360
      X2              =   6600
      Y1              =   4440
      Y2              =   4440
   End
   Begin VB.Label Label8 
      AutoSize        =   -1  'True
      Caption         =   "금액"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   9
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   225
      Left            =   840
      TabIndex        =   41
      Top             =   1695
      Width           =   360
   End
   Begin VB.Label Label7 
      AutoSize        =   -1  'True
      Caption         =   "Server IP"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   9
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   225
      Left            =   480
      TabIndex        =   36
      Top             =   3165
      Width           =   705
   End
   Begin VB.Label Label9 
      AutoSize        =   -1  'True
      Caption         =   "Server Port"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   9
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   225
      Left            =   3120
      TabIndex        =   35
      Top             =   3165
      Width           =   885
   End
   Begin VB.Label Label6 
      AutoSize        =   -1  'True
      Caption         =   "서명데이터"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   9
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   225
      Left            =   360
      TabIndex        =   32
      Top             =   2775
      Width           =   900
   End
   Begin VB.Label Label5 
      AutoSize        =   -1  'True
      Caption         =   "승인날짜"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   9
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   225
      Left            =   4920
      TabIndex        =   12
      Top             =   1695
      Width           =   720
   End
   Begin VB.Label Label4 
      AutoSize        =   -1  'True
      Caption         =   "승인번호"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   9
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   225
      Left            =   2520
      TabIndex        =   10
      Top             =   1695
      Width           =   720
   End
   Begin VB.Label Label3 
      AutoSize        =   -1  'True
      Caption         =   "바코드번호"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   9
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   225
      Left            =   360
      TabIndex        =   6
      Top             =   1335
      Width           =   900
   End
   Begin VB.Label Label2 
      AutoSize        =   -1  'True
      Caption         =   "응답전문"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   9
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   225
      Left            =   480
      TabIndex        =   4
      Top             =   495
      Width           =   720
   End
   Begin VB.Label Label1 
      AutoSize        =   -1  'True
      Caption         =   "요청전문"
      BeginProperty Font 
         Name            =   "맑은 고딕"
         Size            =   9
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   225
      Left            =   480
      TabIndex        =   3
      Top             =   165
      Width           =   720
   End
End
Attribute VB_Name = "Form1"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Private Declare Function NICEVCATB Lib "C:\NICEVCAT\NVCAT.dll" (ByVal send_data As String, ByRef recv_data As Byte) As Long
Private Declare Function Set_SvrInfo Lib "C:\NICEVCAT\NVCAT.dll" (ByVal ip As String, ByVal port As String) As Long
Private Declare Function REQ_STOP Lib "C:\NICEVCAT\NVCAT.dll" () As Long
Private Declare Function REQ_BARCODE Lib "C:\NICEVCAT\NVCAT.dll" (ByVal hwtype As String, ByRef recv_data As Byte) As Long

Private Sub Command1_Click() 'NICEVCATB
    Dim FS As String
    FS = Chr$(&H1C)

    Dim ret As Long
    Dim bReceData(1024) As Byte
    
    If Len(SendData.Text) > 0 Then
        ret = NICEVCATB(SendData.Text, bReceData(0))
        MsgBox (ret)
        RecvData.Text = StrConv(bReceData, vbUnicode)
        If ret = 1 Then
            RecvParser (RecvData.Text)
        End If
    Else
        MsgBox ("요청전문 확인")

    End If
    
End Sub

Private Sub Command25_Click() '알리위챗페이/카카오페이/SSGPAY/L.PAY/제로페이/DGB유페이 승인 (PAYPRO)
    '거래구분 : 0300 (포인트승인)
    '거래유형 : 10 (신용)
    'WCC : L (1차원바코드)
    '전문TEXT : PRO (PAYPRO)
    Dim FS As String
    FS = Chr$(&H1C)

    Dim ret As Long
    Dim bReceData(2048) As Byte
    
    SendData.Text = "0300" + FS + "10" + FS + "L" + FS + Money.Text + FS + "0" + FS + "0" + FS + "00" + FS + "" + FS + "" + FS + "" + FS + FS + FS + Barcode.Text + FS + FS + FS + FS + Textno.Text + FS + ApprFiller.Text + FS + ApprPersonno.Text + FS + "PRO" + FS + "" + FS + ApprDealno.Text + FS + FS + FS + SignData.Text + FS + MPAddInfoYN.Text + FS + MPBizCode.Text + FS + MPAddInfo.Text + FS + MPFiller2.Text + FS + FS
    
    ret = NICEVCATB(SendData.Text, bReceData(0))
    
    MsgBox (ret)
    RecvData.Text = StrConv(bReceData, vbUnicode)
    If ret = 1 Then
        RecvParser (RecvData.Text)
    End If
End Sub

Private Sub Command24_Click() '알리위챗페이/카카오페이/SSGPAY/L.PAY/제로페이/DGB유페이 취소 (PAYPRO)
    '거래구분 : 0520 (포인트승인)
    '거래유형 : 10 (신용)
    'WCC : L (1차원바코드)
    '전문TEXT : PRO (PAYPRO)
    '원거래승인번호, 원거래승인날짜(YYMMDD) 필수
    Dim FS As String
    FS = Chr$(&H1C)

    Dim ret As Long
    Dim bReceData(2048) As Byte
    
    SendData.Text = "0520" + FS + "10" + FS + "L" + FS + Money.Text + FS + "0" + FS + "0" + FS + "00" + FS + Apprno.Text + FS + Apprdate.Text + FS + "" + FS + FS + FS + Barcode.Text + FS + FS + FS + FS + Textno.Text + FS + ApprFiller.Text + FS + ApprPersonno.Text + FS + "PRO" + FS + "" + FS + ApprDealno.Text + FS + FS + FS + SignData.Text + FS + MPAddInfoYN.Text + FS + MPBizCode.Text + FS + MPAddInfo.Text + FS + MPFiller2.Text + FS + FS
    
    ret = NICEVCATB(SendData.Text, bReceData(0))
    
    MsgBox (ret)
    RecvData.Text = StrConv(bReceData, vbUnicode)
    If ret = 1 Then
        RecvParser (RecvData.Text)
    End If
End Sub

Private Sub Command20_Click() 'BC/은련QR승인
    'UNIQR승인
    '거래구분 : 0340 (비씨QR/은련QR승인)
    '거래유형 : 10 (신용)
    'WCC : G (QRIC)
    'QRIC번호 : 리딩데이터
    Dim FS As String
    FS = Chr$(&H1C)

    Dim ret As Long
    Dim bReceData(1024) As Byte
    
    SendData.Text = "0340" + FS + "10" + FS + "G" + FS + Money.Text + FS + "0" + FS + "0" + FS + "00" + FS + "" + FS + "" + FS + "" + FS + FS + FS + Barcode.Text + FS + FS + FS + FS + FS + "" + FS + FS + "" + FS + "" + FS + FS + FS + FS + SignData.Text + FS
          
    ret = NICEVCATB(SendData.Text, bReceData(0))
    
    MsgBox (ret)
    RecvData.Text = StrConv(bReceData, vbUnicode)
    If ret = 1 Then
        RecvParser (RecvData.Text)
    End If
End Sub

Private Sub Command21_Click() 'BC/은련QR취소
    'UNIQR취소
    '거래구분 : 0560 (비씨QR/은련QR취소)
    'WCC : G (QRIC)
    '거래유형 : 10 (신용)
    'QRIC번호 : 리딩데이터
    '원거래승인번호, 원거래승인날짜(YYMMDD) 필수
    Dim FS As String
    FS = Chr$(&H1C)

    Dim ret As Long
    Dim bReceData(1024) As Byte
    
    SendData.Text = "0560" + FS + "10" + FS + "G" + FS + Money.Text + FS + "0" + FS + "0" + FS + "00" + FS + Apprno.Text + FS + Apprdate.Text + FS + "" + FS + FS + FS + Barcode.Text + FS + FS + FS + FS + FS + "" + FS + FS + "" + FS + "" + FS + FS + FS + FS + SignData.Text + FS
         
    ret = NICEVCATB(SendData.Text, bReceData(0))
    
    MsgBox (ret)
    RecvData.Text = StrConv(bReceData, vbUnicode)
    If ret = 1 Then
        RecvParser (RecvData.Text)
    End If
End Sub

Private Sub Command26_Click()
    '앱카드승인
    '거래구분 : 0300 (포인트승인)
    '거래유형 : 10 (신용)
    'WCC : L (1차원바코드)
    '전문TEXT : ACD (앱카드)
    Dim FS As String
    FS = Chr$(&H1C)

    Dim ret As Long
    Dim bReceData(1024) As Byte
    
    SendData.Text = "0300" + FS + "10" + FS + "L" + FS + Money.Text + FS + "0" + FS + "0" + FS + "00" + FS + "" + FS + "" + FS + "" + FS + FS + FS + Barcode.Text + FS + FS + FS + FS + FS + "" + FS + FS + "ACD" + FS + "" + FS + FS + FS + FS + SignData.Text + FS
        
    ret = NICEVCATB(SendData.Text, bReceData(0))
    
    MsgBox (ret)
    RecvData.Text = StrConv(bReceData, vbUnicode)
    If ret = 1 Then
        RecvParser (RecvData.Text)
    End If
End Sub

Private Sub Command27_Click()
    '앱카드취소
    '거래구분 : 0520 (포인트취소)
    '거래유형 : 10 (신용)
    'WCC : L (1차원바코드)
    '전문TEXT : HPS (일반)
    '취소시 원거래승인번호는 원거래고유번호필드
    '취소시 원거래승인날짜는 YYMMDD
    Dim FS As String
    FS = Chr$(&H1C)

    Dim ret As Long
    Dim bReceData(1024) As Byte
    
    SendData.Text = "0520" + FS + "10" + FS + "L" + FS + Money.Text + FS + "0" + FS + "0" + FS + "00" + FS + Apprno.Text + FS + Apprdate.Text + FS + "" + FS + FS + FS + Barcode.Text + FS + FS + FS + FS + FS + "" + FS + FS + "ACD" + FS + "" + FS + FS + FS + FS + SignData.Text + FS
        
    ret = NICEVCATB(SendData.Text, bReceData(0))
    
    MsgBox (ret)
    RecvData.Text = StrConv(bReceData, vbUnicode)
    If ret = 1 Then
        RecvParser (RecvData.Text)
    End If
End Sub

Private Sub Command28_Click()
    '카카오페이머니 승인인증
    '거래구분 : 0300 (포인트승인)
    '거래유형 : 10 (신용)
    'WCC : L (1차원바코드)
    '포인트바코드번호 : 카카오페이 바코드
    '전문TEXT : KKS (카카오페이인증)
    Dim FS As String
    FS = Chr$(&H1C)

    Dim ret As Long
    Dim bReceData(1024) As Byte
    
    SendData.Text = "0300" + FS + "10" + FS + "L" + FS + Money.Text + FS + "0" + FS + "0" + FS + "00" + FS + "" + FS + "" + FS + "" + FS + FS + FS + Barcode.Text + FS + FS + FS + FS + FS + "" + FS + FS + "KKS" + FS + "" + FS + FS + FS + FS + SignData.Text + FS
        
    ret = NICEVCATB(SendData.Text, bReceData(0))
    
    MsgBox (ret)
    RecvData.Text = StrConv(bReceData, vbUnicode)
    If ret = 1 Then
        RecvParser (RecvData.Text)
    End If
End Sub

Private Sub Command29_Click()
    '카카오머니승인
    '거래구분 : 0300 (포인트승인)
    '거래유형 : 10 (신용)
    'WCC : L (1차원바코드)
    '전문TEXT : KKE (카카오페이승인)
    '포인트바코드번호 : 카카오페이 바코드
    '서명패드표시금액 : MONY
    'IPADDRESS : KKE+최초요청금액(9) (예:최초요청금액 전원이면 KKE000001000)
    Dim FS As String
    FS = Chr$(&H1C)

    Dim ret As Long
    Dim bReceData(1024) As Byte
    
    SendData.Text = "0300" + FS + "10" + FS + "L" + FS + Money.Text + FS + "0" + FS + "0" + FS + "00" + FS + "" + FS + "" + FS + "" + FS + FS + FS + Barcode.Text + FS + FS + FS + FS + FS + "" + "      " + Text29.Text + "07" + FS + "MONY         " + FS + "KKE" + FS + "" + FS + FS + FS + "KKE00000" + Money.Text + FS + SignData.Text + FS
        
    ret = NICEVCATB(SendData.Text, bReceData(0))
    
    MsgBox (ret)
    RecvData.Text = StrConv(bReceData, vbUnicode)
    If ret = 1 Then
        RecvParser (RecvData.Text)
    End If
End Sub

Private Sub Command30_Click()
    '카카오카드승인
    '거래구분 : 0300 (포인트승인)
    '거래유형 : 10 (신용)
    'WCC : L (1차원바코드)
    '전문TEXT : KKE (카카오페이승인)
    '포인트바코드번호 : 인증시 카드BIN 필드에 수신받은 카카오페이OTC
    '서명패드표시금액 : CARD+카카오 자체할인금액 (인증시 발생포인트 필드에 수신받은 자체할인금액)(9)
    'IPADDRESS : KKE+최초요청금액(9) (예:최초요청금액 전원이면 KKE000001000)
    Dim FS As String
    FS = Chr$(&H1C)

    Dim ret As Long
    Dim bReceData(1024) As Byte
    
    SendData.Text = "0300" + FS + "10" + FS + "L" + FS + Money.Text + FS + "0" + FS + "0" + FS + "00" + FS + "" + FS + "" + FS + "" + FS + FS + FS + Barcode.Text + FS + FS + FS + FS + FS + "" + "      " + Text29.Text + "07" + FS + "CARD000000000" + FS + "KKE" + FS + "" + FS + FS + FS + "KKE00000" + Money.Text + FS + SignData.Text + FS
        
    ret = NICEVCATB(SendData.Text, bReceData(0))
    
    MsgBox (ret)
    RecvData.Text = StrConv(bReceData, vbUnicode)
    If ret = 1 Then
        RecvParser (RecvData.Text)
    End If
End Sub

Private Sub Command31_Click()
    '카카오카드취소
    '거래구분 : 0520 (포인트취소)
    '거래유형 : 10 (신용)
    'WCC : L (1차원바코드)
    '전문TEXT : KKE (카카오페이승인)
    '포인트바코드번호 : 인증시 카드BIN 필드에 수신받은 카카오페이OTC
    '서명패드표시금액 : CARD+카카오 자체할인금액 (인증시 발생포인트 필드에 수신받은 자체할인금액)(9)
    'IPADDRESS : KKE+최초요청금액(9) (예:최초요청금액 전원이면 KKE000001000)
    '승인번호 / 승인날짜 필수
    '원거래일자 : 원거래일자(YYMMDD)
    '원거래고유번호 : 원거래승인번호
    Dim FS As String
    FS = Chr$(&H1C)

    Dim ret As Long
    Dim bReceData(1024) As Byte
    
    SendData.Text = "0520" + FS + "10" + FS + "L" + FS + Money.Text + FS + "0" + FS + "0" + FS + "00" + FS + "" + FS + Apprdate.Text + FS + "" + FS + FS + FS + Barcode.Text + FS + FS + FS + FS + FS + "" + "      " + Text29.Text + "07" + FS + "CARD000000000" + FS + "KKE" + FS + "" + FS + Apprno.Text + FS + FS + "KKE00000" + Money.Text + FS + SignData.Text + FS
        
    ret = NICEVCATB(SendData.Text, bReceData(0))
    
    MsgBox (ret)
    RecvData.Text = StrConv(bReceData, vbUnicode)
    If ret = 1 Then
        RecvParser (RecvData.Text)
    End If
End Sub

Private Sub Command32_Click()
    '카카오머니취소
    '거래구분 : 0520 (포인트취소)
    '거래유형 : 10 (신용)
    'WCC : L (1차원바코드)
    '전문TEXT : KKE (카카오페이승인)
    '포인트바코드번호 : 카카오페이 바코드
    '서명패드표시금액 : MONY
    'IPADDRESS : KKE+최초요청금액(9) (예:최초요청금액 전원이면 KKE000001000)
    '원거래일자 : 원거래일자(YYMMDD)
    '원거래고유번호 : 원거래승인번호
    Dim FS As String
    FS = Chr$(&H1C)

    Dim ret As Long
    Dim bReceData(1024) As Byte
    
    SendData.Text = "0520" + FS + "10" + FS + "L" + FS + Money.Text + FS + "0" + FS + "0" + FS + "00" + FS + "" + FS + Apprdate.Text + FS + "" + FS + FS + FS + Barcode.Text + FS + FS + FS + FS + FS + "" + "      " + Text29.Text + "07" + FS + "MONY         " + FS + "KKE" + FS + "" + FS + Apprno.Text + FS + FS + "KKE00000" + Money.Text + FS + SignData.Text + FS
        
    ret = NICEVCATB(SendData.Text, bReceData(0))
    
    MsgBox (ret)
    RecvData.Text = StrConv(bReceData, vbUnicode)
    If ret = 1 Then
        RecvParser (RecvData.Text)
    End If
End Sub



Private Sub Command33_Click()
    '카카오페이머니 취소인증
    '거래구분 : 0520 (포인트취소)
    '거래유형 : 10 (신용)
    'WCC : L (1차원바코드)
    '포인트바코드번호 : 카카오페이 바코드
    '전문TEXT : KKS (카카오페이인증)
    '승인번호 / 승인날짜 필수
    '원거래일자 : 원거래일자(YYMMDD)
    '원거래고유번호 : 원거래승인번호
    Dim FS As String
    FS = Chr$(&H1C)

    Dim ret As Long
    Dim bReceData(1024) As Byte
    
    SendData.Text = "0520" + FS + "10" + FS + "L" + FS + Money.Text + FS + "0" + FS + "0" + FS + "00" + FS + "" + FS + Apprdate.Text + FS + "" + FS + FS + FS + Barcode.Text + FS + FS + FS + FS + FS + "" + FS + FS + "KKS" + FS + "" + FS + Apprno.Text + FS + FS + FS + SignData.Text + FS
        
    ret = NICEVCATB(SendData.Text, bReceData(0))
    
    MsgBox (ret)
    RecvData.Text = StrConv(bReceData, vbUnicode)
    If ret = 1 Then
        RecvParser (RecvData.Text)
    End If
End Sub

Private Sub Command34_Click()
Dim ret As Long
    
    Dim bRecvData(3000) As Byte
    ret = REQ_BARCODE("2", bRecvData(0))
    
    MsgBox (ret)
    
    If ret <> 1 Then
        MsgBox ("리턴값 확인하세요")
        Exit Sub
    End If
    
    MsgBox ("응답데이터 : " + StrConv(bRecvData, vbUnicode))
    Barcode.Text = StrConv(bRecvData, vbUnicode)
End Sub

Private Sub Command35_Click()
    '거래구분 : 0300 (포인트승인)
    '거래유형 : 10 (신용)
    'WCC : L(운전면허)
    '전문TEXT : MDL (PASS 모바일 운전면허/신분증)
    '거래금액 : 성인여부(1012002)
    '원거래승인번호 : 성인기준구분코드(1043003)
    Dim FS As String
    FS = Chr$(&H1C)

    Dim ret As Long
    Dim bReceData(2048) As Byte
    
    SendData.Text = "0300" + FS + "10" + FS + "L" + FS + "1012002" + FS + FS + FS + "00" + FS + "1043003" + FS + FS + FS + FS + FS + Barcode.Text + FS + FS + FS + FS + FS + FS + FS + "MDL" + FS + FS + FS + FS + FS + FS
    
    ret = NICEVCATB(SendData.Text, bReceData(0))
    
    MsgBox (ret)
    RecvData.Text = StrConv(bReceData, vbUnicode)
    If ret = 1 Then
        RecvParser (RecvData.Text)
    End If
End Sub

Private Sub Command36_Click()
    '거래구분 : 0300 (포인트승인)
    '거래유형 : 10 (신용)
    'WCC : Q(주민번호)
    '전문TEXT : MDL (PASS 모바일 운전면허/신분증)
    '거래금액 : 성인여부(1012002)
    '원거래승인번호 : 성인기준구분코드(1043003)
    Dim FS As String
    FS = Chr$(&H1C)

    Dim ret As Long
    Dim bReceData(2048) As Byte
    
    SendData.Text = "0300" + FS + "10" + FS + "Q" + FS + "1012002" + FS + FS + FS + "00" + FS + "1043003" + FS + FS + FS + FS + FS + Barcode.Text + FS + FS + FS + FS + FS + FS + FS + "MDL" + FS + FS + FS + FS + FS + FS
    
    ret = NICEVCATB(SendData.Text, bReceData(0))
    
    MsgBox (ret)
    RecvData.Text = StrConv(bReceData, vbUnicode)
    If ret = 1 Then
        RecvParser (RecvData.Text)
    End If
End Sub

Private Sub Command37_Click()
    '거래구분 : 0300 (포인트승인)
    '거래유형 : 10 (신용)
    'WCC : L (1차원바코드)
    '전문TEXT : PPR (페이코)
    '부가정보여부 : Y
    'Filler2 :"PAYCO" + 거래구분(2) + PAYCO일련번호(20) + "C" + 신용카드금액(9) + "P" + 포인트거래금액(9) + "O" + 쿠폰금액(9) + "T" + (쿠폰금액제외)신용 or 포인트 금액의 세금
    Dim FS As String
    FS = Chr$(&H1C)

    Dim ret As Long
    Dim bReceData(2048) As Byte
    
    MPAddInfoYN.Text = "Y"
    MPFiller2.Text = "PAYCO032025043010525405    C000000000P000001004O000000000                                                       "
    
    SendData.Text = "0300" + FS + "10" + FS + "L" + FS + Money.Text + FS + "0" + FS + "0" + FS + "00" + FS + "" + FS + "" + FS + "" + FS + FS + FS + Barcode.Text + FS + FS + FS + FS + Textno.Text + FS + ApprFiller.Text + FS + FS + "PPR" + FS + "" + FS + ApprDealno.Text + FS + FS + FS + SignData.Text + FS + MPAddInfoYN.Text + FS + MPBizCode.Text + FS + MPAddInfo.Text + FS + MPFiller2.Text + FS + FS
    
    ret = NICEVCATB(SendData.Text, bReceData(0))
    
    MsgBox (ret)
    RecvData.Text = StrConv(bReceData, vbUnicode)
    If ret = 1 Then
        RecvParser (RecvData.Text)
    End If
End Sub

Private Sub Command38_Click()
    '거래구분 : 0520 (포인트승인)
    '거래유형 : 10 (신용)
    'WCC : L (1차원바코드)
    '전문TEXT : PPR (페이코)
    '원거래승인번호, 원거래승인날짜(YYMMDD) 필수
    '부가정보여부 : Y
    'Filler2 :"PAYCO" + 거래구분(2) + PAYCO일련번호(20) + "C" + 신용카드금액(9) + "P" + 포인트거래금액(9) + "O" + 쿠폰금액(9) + "T" + (쿠폰금액제외)신용 or 포인트 금액의 세금
    Dim FS As String
    FS = Chr$(&H1C)

    Dim ret As Long
    Dim bReceData(2048) As Byte
    
    MPAddInfoYN.Text = "Y"
    MPFiller2.Text = "PAYCO032025043010525405    C000000000P000001004O000000000                                                       "
    
    SendData.Text = "0520" + FS + "10" + FS + "L" + FS + Money.Text + FS + "0" + FS + "0" + FS + "00" + FS + Apprno.Text + FS + Apprdate.Text + FS + "" + FS + FS + FS + Barcode.Text + FS + FS + FS + FS + Textno.Text + FS + ApprFiller.Text + FS + FS + "PPR" + FS + "" + FS + ApprDealno.Text + FS + FS + FS + SignData.Text + FS + MPAddInfoYN.Text + FS + MPBizCode.Text + FS + MPAddInfo.Text + FS + MPFiller2.Text + FS + FS
    
    ret = NICEVCATB(SendData.Text, bReceData(0))
    
    MsgBox (ret)
    RecvData.Text = StrConv(bReceData, vbUnicode)
    If ret = 1 Then
        RecvParser (RecvData.Text)
    End If
End Sub

Private Sub Command6_Click() '현금영수증승인
    '현금영수증승인
    '거래구분 : 0300 (포인트승인)
    '거래유형 : 21 (현금)
    'WCC : P (POS입력)
    '전문TEXT : HPS (일반)
    '할부개월 : 01(소비자), 02(사업자)
    Dim FS As String
    FS = Chr$(&H1C)

    Dim ret As Long
    Dim bReceData(1024) As Byte
    
    SendData.Text = "0300" + FS + "21" + FS + "P" + FS + Money.Text + FS + "0" + FS + "0" + FS + "01" + FS + "" + FS + "" + FS + "" + FS + FS + FS + Barcode.Text + FS + FS + FS + FS + FS + "" + FS + FS + "HPS" + FS + "H1" + FS + ApprDealno.Text + FS + FS + FS
        
    ret = NICEVCATB(SendData.Text, bReceData(0))
    
    MsgBox (ret)
    RecvData.Text = StrConv(bReceData, vbUnicode)
    If ret = 1 Then
        RecvParser (RecvData.Text)
    End If
End Sub

Private Sub Command7_Click() '현금영수증취소
    '현금영수증취소
    '거래구분 : 0520 (포인트취소)
    'WCC : P (POS입력)
    '거래유형 : 21 (현금)
    '전문TEXT : HPS (일반)
    '원거래승인번호(020185419 => 20185419), 원거래승인날짜(YYMMDD) 필수
    '할부개월 : 01(소비자), 02(사업자)
    Dim FS As String
    FS = Chr$(&H1C)

    Dim ret As Long
    Dim bReceData(1024) As Byte
    
    SendData.Text = "0520" + FS + "21" + FS + "P" + FS + Money.Text + FS + "0" + FS + "0" + FS + "01" + FS + Apprno.Text + FS + Apprdate.Text + FS + "" + FS + FS + FS + Barcode.Text + FS + FS + FS + FS + FS + "" + FS + FS + "HPS" + FS + "" + FS + FS + FS + FS + FS
        
    ret = NICEVCATB(SendData.Text, bReceData(0))
    
    MsgBox (ret)
    RecvData.Text = StrConv(bReceData, vbUnicode)
    If ret = 1 Then
        'RecvParser (RecvData.Text)
    End If
End Sub

Private Sub Command11_Click() 'SKT승인
    'SKT승인
    '거래구분 : 0300 (포인트승인)
    '거래유형 : 70 (SKT)
    'WCC : P(POS입력)
    '전문TEXT : HPS (일반)
    Dim FS As String
    FS = Chr$(&H1C)

    Dim ret As Long
    Dim bReceData(1024) As Byte
    
    SendData.Text = "0300" + FS + "70" + FS + "P" + FS + Money.Text + FS + "0" + FS + "0" + FS + "00" + FS + "" + FS + "" + FS + "" + FS + FS + FS + Barcode.Text + FS + FS + FS + FS + FS + "" + FS + FS + "HPS" + FS + "" + FS + FS + FS + FS + FS
        
    ret = NICEVCATB(SendData.Text, bReceData(0))
    
    MsgBox (ret)
    RecvData.Text = StrConv(bReceData, vbUnicode)
    If ret = 1 Then
        RecvParser (RecvData.Text)
    End If
End Sub

Private Sub Command10_Click() 'SKT취소
    'SKT취소
    '거래구분 : 0520 (포인트취소)
    '거래유형 : 70 (SKT)
    'WCC : P(POS입력)
    '전문TEXT : HPS (일반)
    '원거래승인번호, 원거래승인날짜(YYMMDD) 필수
    Dim FS As String
    FS = Chr$(&H1C)

    Dim ret As Long
    Dim bReceData(1024) As Byte
    
    SendData.Text = "0520" + FS + "70" + FS + "P" + FS + Money.Text + FS + "0" + FS + "0" + FS + "00" + FS + Apprno.Text + FS + Apprdate.Text + FS + "" + FS + FS + FS + Barcode.Text + FS + FS + FS + FS + FS + "" + FS + FS + "HPS" + FS + "" + FS + FS + FS + FS + FS
        
    ret = NICEVCATB(SendData.Text, bReceData(0))
    
    MsgBox (ret)
    RecvData.Text = StrConv(bReceData, vbUnicode)
    If ret = 1 Then
        RecvParser (RecvData.Text)
    End If
End Sub

Private Sub Command8_Click() '유플러스승인
    '유플러스승인
    '거래구분 : 0300 (포인트승인)
    '거래유형 : 90 (LGT)
    'WCC : P(POS입력)
    '전문TEXT : HPS (일반)
    Dim FS As String
    FS = Chr$(&H1C)

    Dim ret As Long
    Dim bReceData(1024) As Byte
    
    SendData.Text = "0300" + FS + "90" + FS + "P" + FS + Money.Text + FS + "0" + FS + "0" + FS + "00" + FS + "" + FS + "" + FS + "" + FS + FS + FS + Barcode.Text + FS + FS + FS + FS + FS + "" + FS + FS + "HPS" + FS + "" + FS + FS + FS + FS + FS
          
    ret = NICEVCATB(SendData.Text, bReceData(0))
    
    MsgBox (ret)
    RecvData.Text = StrConv(bReceData, vbUnicode)
    If ret = 1 Then
        RecvParser (RecvData.Text)
    End If
End Sub

Private Sub Command9_Click() '유플러스취소
    '유플러스취소
    '거래구분 : 0520 (포인트취소)
    '거래유형 : 90 (LGT)
    'WCC : P(POS입력)
    '전문TEXT : HPS (일반)
    '원거래승인번호, 원거래승인날짜(YYMMDD) 필수
    Dim FS As String
    FS = Chr$(&H1C)

    Dim ret As Long
    Dim bReceData(1024) As Byte
    
    SendData.Text = "0520" + FS + "90" + FS + "P" + FS + Money.Text + FS + "0" + FS + "0" + FS + "00" + FS + Apprno.Text + FS + Apprdate.Text + FS + "" + FS + FS + FS + Barcode.Text + FS + FS + FS + FS + FS + "" + FS + FS + "HPS" + FS + "" + FS + FS + FS + FS + FS
        
    ret = NICEVCATB(SendData.Text, bReceData(0))
    
    MsgBox (ret)
    RecvData.Text = StrConv(bReceData, vbUnicode)
    If ret = 1 Then
        RecvParser (RecvData.Text)
    End If
End Sub

Private Sub Command12_Click() 'KT승인
    'KT승인
    '거래구분 : 0320 (멤버쉽승인)
    '거래유형 : A1 (KT)
    'WCC : P(POS입력)
    '전문TEXT : HPS (일반)
    Dim FS As String
    FS = Chr$(&H1C)

    Dim ret As Long
    Dim bReceData(1024) As Byte
    
    SendData.Text = "0320" + FS + "A1" + FS + "P" + FS + Money.Text + FS + "00" + FS + "02" + FS + "" + FS + "" + FS + "" + FS + "" + FS + FS + FS + Barcode.Text + FS + FS + FS + FS + FS + "" + FS + FS + "HPS" + FS + FS + FS + FS + FS + FS
     
    ret = NICEVCATB(SendData.Text, bReceData(0))
    
    MsgBox (ret)
    RecvData.Text = StrConv(bReceData, vbUnicode)
    If ret = 1 Then
        RecvParser (RecvData.Text)
    End If
End Sub

Private Sub Command13_Click() 'KT취소
    'KT취소
    '거래구분 : 0540 (멤버쉽취소)
    '거래유형 : A1 (KT)
    'WCC : P(POS입력)
    '전문TEXT : HPS (일반)
    '원거래승인번호, 원거래승인날짜(YYMMDD) 필수
    Dim FS As String
    FS = Chr$(&H1C)

    Dim ret As Long
    Dim bReceData(1024) As Byte
    
    SendData.Text = "0540" + FS + "A1" + FS + "P" + FS + Money.Text + FS + "00" + FS + "12" + FS + "" + FS + Apprno.Text + FS + Apprdate.Text + FS + "" + FS + FS + FS + Barcode.Text + FS + FS + FS + FS + FS + "" + FS + FS + "HPS" + FS + FS + FS + FS + FS + FS
        
    ret = NICEVCATB(SendData.Text, bReceData(0))
    
    MsgBox (ret)
    RecvData.Text = StrConv(bReceData, vbUnicode)
    If ret = 1 Then
        RecvParser (RecvData.Text)
    End If
End Sub

Private Sub Command14_Click() '캐시백승인
    '캐시백승인
    '거래구분 : 0320 (멤버쉽승인)
    '거래유형 : 40 (캐시백)
    'WCC : P(POS입력)
    '전문TEXT : HPS (일반)
    Dim FS As String
    FS = Chr$(&H1C)

    Dim ret As Long
    Dim bReceData(1024) As Byte
    
    SendData.Text = "0320" + FS + "40" + FS + "P" + FS + Money.Text + FS + "00" + FS + "01" + FS + "" + FS + "" + FS + "" + FS + "" + FS + FS + FS + Barcode.Text + FS + FS + FS + FS + FS + "" + FS + FS + "HPS" + FS + FS + FS + FS + FS + FS
        
    ret = NICEVCATB(SendData.Text, bReceData(0))
    
    MsgBox (ret)
    RecvData.Text = StrConv(bReceData, vbUnicode)
    If ret = 1 Then
        RecvParser (RecvData.Text)
    End If
End Sub

Private Sub Command15_Click()
    '캐시백취소
    '거래구분 : 0540 (멤버쉽취소)
    '거래유형 : 40 (캐시백)
    'WCC : P(POS입력)
    '전문TEXT : HPS (일반)
    '원거래승인번호, 원거래승인날짜(YYMMDD) 필수
    Dim FS As String
    FS = Chr$(&H1C)

    Dim ret As Long
    Dim bReceData(1024) As Byte
    
    SendData.Text = "0540" + FS + "40" + FS + "P" + FS + Money.Text + FS + "00" + FS + "11" + FS + "" + FS + Apprno.Text + FS + Apprdate.Text + FS + "" + FS + FS + FS + Barcode.Text + FS + FS + FS + FS + FS + "" + FS + FS + "HPS" + FS + FS + FS + FS + FS + FS
        
    ret = NICEVCATB(SendData.Text, bReceData(0))
    
    MsgBox (ret)
    RecvData.Text = StrConv(bReceData, vbUnicode)
    If ret = 1 Then
        RecvParser (RecvData.Text)
    End If
End Sub

Private Sub Command16_Click() '위쳇페이승인
    '위쳇페이승인
    '거래구분 : 0300 (포인트승인)
    '거래유형 : 10 (신용)
    'WCC : P (POS입력)
    '전문TEXT : WCP (위챗페이)
    '거래고유번호 : 410 (원화)
    '전문관리번호 : "2001" + Format(Now(), "yyMMddHHmmss") + Format(Int(10000 * Rnd), "0000")
    Dim FS As String
    FS = Chr$(&H1C)

    Dim ret As Long
    Dim bReceData(1024) As Byte
    
    SendData.Text = "0300" + FS + "10" + FS + "P" + FS + Money.Text + FS + "0" + FS + "0" + FS + "00" + FS + "" + FS + "" + FS + "" + FS + FS + FS + Barcode.Text + FS + FS + FS + FS + "2001" + Format(Now(), "yyMMddHHmmss") + Format(Int(10000 * Rnd), "0000") + FS + "" + FS + FS + "WCP" + FS + "" + FS + "410" + FS + FS + FS + SignData.Text + FS
        
    ret = NICEVCATB(SendData.Text, bReceData(0))
    
    MsgBox (ret)
    RecvData.Text = StrConv(bReceData, vbUnicode)
    If ret = 1 Then
        RecvParser (RecvData.Text)
    End If
End Sub

Private Sub Command17_Click() '위쳇페이취소
    '위쳇페이취소
    '거래구분 : 0520 (포인트취소)
    'WCC : P (POS입력)
    '거래유형 : 10 (신용)
    '전문TEXT : WCP (위챗페이)
    '거래고유번호 : 410 (원화)
    '전문관리번호 : 승인시전문관리번호
    '승인날짜(YYMMDD) 필수
    '승인시전문관리번호로 취소하기 때문에 바코드번호 필요없음
    Dim FS As String
    FS = Chr$(&H1C)

    Dim ret As Long
    Dim bReceData(1024) As Byte
    
    SendData.Text = "0520" + FS + "10" + FS + "P" + FS + Money.Text + FS + "0" + FS + "0" + FS + "00" + FS + "" + FS + Apprdate.Text + FS + "" + FS + FS + FS + "" + FS + FS + FS + FS + Textno + FS + "" + FS + FS + "WCP" + FS + "" + FS + "410" + FS + FS + FS + SignData.Text + FS
        
    ret = NICEVCATB(SendData.Text, bReceData(0))
    
    MsgBox (ret)
    RecvData.Text = StrConv(bReceData, vbUnicode)
    If ret = 1 Then
        RecvParser (RecvData.Text)
    End If
End Sub

Private Sub Command19_Click() '알리페이승인
    '알리페이승인
    '거래구분 : 0300 (포인트승인)
    '거래유형 : 10 (신용)
    'WCC : P (POS입력)
    '전문TEXT : ALP (알리페이)
    '거래고유번호 : 410 (원화)
    '전문관리번호 : "2301" + Format(Now(), "yyMMddHHmmss") + Format(Int(10000 * Rnd), "0000")
    Dim FS As String
    FS = Chr$(&H1C)

    Dim ret As Long
    Dim bReceData(1024) As Byte
    
    SendData.Text = "0300" + FS + "10" + FS + "P" + FS + Money.Text + FS + "0" + FS + "0" + FS + "00" + FS + "" + FS + "" + FS + "" + FS + FS + FS + Barcode.Text + FS + FS + FS + FS + "2301" + Format(Now(), "yyMMddHHmmss") + Format(Int(10000 * Rnd), "0000") + FS + "" + FS + ApprPersonno.Text + FS + "ALP" + FS + "" + FS + "" + FS + FS + FS + SignData.Text + FS
        
    ret = NICEVCATB(SendData.Text, bReceData(0))
    
    MsgBox (ret)
    RecvData.Text = StrConv(bReceData, vbUnicode)
    If ret = 1 Then
        RecvParser (RecvData.Text)
    End If
End Sub

Private Sub Command18_Click() '알리페이취소
    '알리페이취소
    '거래구분 : 0520 (포인트취소)
    '거래유형 : 10 (신용)
    'WCC : P (POS입력)
    '전문TEXT : ALP (알리페이)
    '거래고유번호 : 410 (원화)
    '전문관리번호 : 승인시전문관리번호
    '승인날짜(YYMMDD) 필수
    '승인시전문관리번호로 취소하기 때문에 바코드번호 필요없음
    Dim FS As String
    FS = Chr$(&H1C)

    Dim ret As Long
    Dim bReceData(1024) As Byte
    
    SendData.Text = "0520" + FS + "10" + FS + "P" + FS + Money.Text + FS + "0" + FS + "0" + FS + "00" + FS + "" + FS + Apprdate.Text + FS + "" + FS + FS + FS + "" + FS + FS + FS + FS + Textno.Text + FS + "" + FS + ApprPersonno.Text + FS + "ALP" + FS + "" + FS + Apprno.Text + FS + FS + FS + SignData.Text + FS
        
    ret = NICEVCATB(SendData.Text, bReceData(0))
    
    MsgBox (ret)
    RecvData.Text = StrConv(bReceData, vbUnicode)
    If ret = 1 Then
        RecvParser (RecvData.Text)
    End If
End Sub

Private Sub Command2_Click() '제로페이승인
    '제로페이승인
    '거래구분 : 0300 (포인트승인)
    '거래유형 : P1 (구매)
    'WCC : L (1차원바코드)
    '전문TEXT : ZRP (제로페이)
    Dim FS As String
    FS = Chr$(&H1C)

    Dim ret As Long
    Dim bReceData(1024) As Byte
    
    SendData.Text = "0300" + FS + "P1" + FS + "L" + FS + Money.Text + FS + "0" + FS + "0" + FS + "00" + FS + "" + FS + "" + FS + "" + FS + FS + FS + Barcode.Text + FS + FS + FS + FS + FS + "" + FS + FS + "ZRP" + FS + "" + FS + FS + FS + FS + FS
        
    ret = NICEVCATB(SendData.Text, bReceData(0))
    
    MsgBox (ret)
    RecvData.Text = StrConv(bReceData, vbUnicode)
    If ret = 1 Then
        RecvParser (RecvData.Text)
    End If
End Sub

Private Sub Command3_Click() '제로페이취소
    '제로페이취소
    '거래구분 : 0520 (포인트취소)
    '거래유형 : P3 (환불)
    'WCC : L (1차원바코드)
    '전문TEXT : ZRP (제로페이)
    '취소시 원거래승인번호는 원거래고유번호필드
    '취소시 원거래승인날짜는 YYMMDD
    Dim FS As String
    FS = Chr$(&H1C)

    Dim ret As Long
    Dim bReceData(1024) As Byte
    
    SendData.Text = "0520" + FS + "P3" + FS + "L" + FS + Money.Text + FS + "0" + FS + "0" + FS + "00" + FS + "" + FS + Apprdate.Text + FS + "" + FS + FS + FS + Barcode.Text + FS + FS + FS + FS + FS + "" + FS + FS + "ZRP" + FS + "" + FS + Apprno.Text + FS + FS + FS + FS
        
    ret = NICEVCATB(SendData.Text, bReceData(0))
    
    MsgBox (ret)
    RecvData.Text = StrConv(bReceData, vbUnicode)
    If ret = 1 Then
        RecvParser (RecvData.Text)
    End If
End Sub

Private Sub Command4_Click() '카카오페이승인
    '카카오페이승인
    '거래구분 : 0300 (포인트승인)
    '거래유형 : 10 (신용)
    'WCC : L (1차원바코드)
    '전문TEXT : KKF (카카오페이)
    Dim FS As String
    FS = Chr$(&H1C)

    Dim ret As Long
    Dim bReceData(1024) As Byte
    
    SendData.Text = "0300" + FS + "10" + FS + "L" + FS + Money.Text + FS + "0" + FS + "0" + FS + "00" + FS + "" + FS + "" + FS + "" + FS + FS + FS + Barcode.Text + FS + FS + FS + FS + FS + "" + FS + FS + "KKF" + FS + "" + FS + FS + FS + FS + SignData.Text + FS
        
    ret = NICEVCATB(SendData.Text, bReceData(0))
    
    MsgBox (ret)
    RecvData.Text = StrConv(bReceData, vbUnicode)
    If ret = 1 Then
        RecvParser (RecvData.Text)
    End If
End Sub

Private Sub Command5_Click() '카카오페이취소
    '거래구분 : 0520 (포인트승인)
    '거래유형 : 10 (신용)
    'WCC : L (1차원바코드)
    '전문TEXT : KKF (카카오페이)
    '원거래승인번호, 원거래승인날짜(YYMMDD) 필수
    Dim FS As String
    FS = Chr$(&H1C)

    Dim ret As Long
    Dim bReceData(1024) As Byte
    
    SendData.Text = "0520" + FS + "10" + FS + "L" + FS + Money.Text + FS + "0" + FS + "0" + FS + "00" + FS + Apprno.Text + FS + Apprdate.Text + FS + "" + FS + FS + FS + Barcode.Text + FS + FS + FS + FS + FS + "" + FS + FS + "KKF" + FS + "" + FS + FS + FS + FS + SignData.Text + FS
        
    ret = NICEVCATB(SendData.Text, bReceData(0))
    
    MsgBox (ret)
    RecvData.Text = StrConv(bReceData, vbUnicode)
    If ret = 1 Then
        RecvParser (RecvData.Text)
    End If
End Sub

Private Sub Command22_Click() '서명요청취소
    Dim ret As Long
    ret = REQ_STOP()
End Sub

Private Sub Command23_Click()
    Dim ret As Long
    ret = Set_SvrInfo(ServerIp.Text, ServerPort.Text)
    MsgBox (ret)
End Sub

Private Sub Form_Load()
    Apprdate.Text = Format(Now, "YYMMDD")
End Sub

Private Sub RecvParser(ByVal recv_data As String)
    Dim FS As String
    FS = Chr$(&H1C)
    
    Dim i, j, k As Long
    Dim maxj As Long
    i = 0
    j = 0
    k = 1
    maxj = 0
    
    Do While i < LenB(recv_data)
        i = i + 1
        If Mid(recv_data, i, 1) = FS Then
            maxj = maxj + 1
        End If
    Loop
        
    i = 0
        Do While 1
            i = i + 1
            If Mid(recv_data, i, 1) = FS Then
                j = j + 1
                
                Select Case (j)
                Case 1
                    Text1.Text = Mid(recv_data, k, i - k)
                Case 2
                    Text2.Text = Mid(recv_data, k, i - k)
                Case 3
                    Text3.Text = Mid(recv_data, k, i - k)
                Case 4
                    Text4.Text = Mid(recv_data, k, i - k)
                Case 5
                    Text5.Text = Mid(recv_data, k, i - k)
                Case 6
                    Text6.Text = Mid(recv_data, k, i - k)
                Case 7
                    Text7.Text = Mid(recv_data, k, i - k)
                Case 8
                    Text8.Text = Mid(recv_data, k, i - k)
                    Apprno.Text = Replace(Text8.Text, " ", "")
                    'If Text2.Text = "21" Then
                    '    Apprno.Text = Mid(Text8.Text, 2, 8)
                    'Else
                    '    Apprno.Text = Mid(Text8.Text, 1, 8)
                    'End If
                Case 9
                    Text9.Text = Mid(recv_data, k, i - k)
                Case 10
                    Text10.Text = Mid(recv_data, k, i - k)
                Case 11
                    Text11.Text = Mid(recv_data, k, i - k)
                Case 12
                    Text12.Text = Mid(recv_data, k, i - k)
                Case 13
                    Text13.Text = Mid(recv_data, k, i - k)
                Case 14
                    Text14.Text = Mid(recv_data, k, i - k)
                Case 15
                    Text15.Text = Mid(recv_data, k, i - k)
                Case 16
                    Text16.Text = Mid(recv_data, k, i - k)
                Case 17
                    Text17.Text = Mid(recv_data, k, i - k)
                Case 18
                    Text18.Text = Mid(recv_data, k, i - k)
                Case 19
                    Text19.Text = Mid(recv_data, k, i - k)
                Case 20
                    Text20.Text = Mid(recv_data, k, i - k)
                Case 21
                    Text21.Text = Mid(recv_data, k, i - k)
                Case 22
                    Text22.Text = Mid(recv_data, k, i - k)
                Case 23
                    Text23.Text = Mid(recv_data, k, i - k)
                Case 24
                    Text24.Text = Mid(recv_data, k, i - k)
                Case 25
                    Text25.Text = Mid(recv_data, k, i - k)
                Case 26
                    Text26.Text = Mid(recv_data, k, i - k)
                Case 27
                    Text27.Text = Mid(recv_data, k, i - k)
                Case 28
                    Text28.Text = Mid(recv_data, k, i - k)
                Case 29
                    Text29.Text = Mid(recv_data, k, i - k)
                Case 30
                    Text30.Text = Mid(recv_data, k, i - k)
                Case 31
                    Text31.Text = Mid(recv_data, k, i - k)
                End Select
                
                k = i + 1
                
                If j = maxj Then '종료
                    Exit Do
                End If
            End If
        Loop
End Sub

