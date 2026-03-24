VERSION 5.00
Begin VB.Form Form1 
   Caption         =   "NVCAT_SAMPLE"
   ClientHeight    =   11730
   ClientLeft      =   60
   ClientTop       =   405
   ClientWidth     =   15840
   LinkTopic       =   "Form1"
   ScaleHeight     =   11730
   ScaleMode       =   0  '사용자
   ScaleWidth      =   22187.19
   Begin VB.CommandButton Command31 
      Caption         =   "결제 2TR 요청 (특정 가맹점)"
      BeginProperty Font 
         Name            =   "굴림"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   315
      Left            =   13200
      TabIndex        =   213
      Top             =   11160
      Width           =   2535
   End
   Begin VB.CommandButton Command30 
      Caption         =   "CHK_CASHIC_CARDBIN (현금IC BIN 조회)"
      BeginProperty Font 
         Name            =   "굴림"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   435
      Left            =   13200
      TabIndex        =   210
      Top             =   10680
      Width           =   2499
   End
   Begin VB.CommandButton Command29 
      Caption         =   "REQ_CASHIC_AL (EMV LABEL 조회)"
      BeginProperty Font 
         Name            =   "굴림"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   435
      Left            =   13200
      TabIndex        =   209
      Top             =   10200
      Width           =   2499
   End
   Begin VB.CommandButton Command19 
      Caption         =   "GetDecSignData(BMP->서명데이터)"
      BeginProperty Font 
         Name            =   "굴림"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   435
      Left            =   13200
      TabIndex        =   208
      Top             =   9720
      Width           =   2499
   End
   Begin VB.CommandButton Command28 
      Caption         =   "REQ_SIGNDATA(서명요청)"
      BeginProperty Font 
         Name            =   "굴림"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   315
      Left            =   13200
      TabIndex        =   206
      Top             =   4560
      Width           =   2499
   End
   Begin VB.Frame Frame9 
      Caption         =   "리더기 펌웨어 업데이트"
      BeginProperty Font 
         Name            =   "굴림"
         Size            =   8.25
         Charset         =   129
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   735
      Left            =   240
      TabIndex        =   199
      Top             =   10800
      Width           =   12855
      Begin VB.CommandButton Command1 
         Caption         =   "리더기 펌웨어 업데이트 요청"
         BeginProperty Font 
            Name            =   "굴림"
            Size            =   8.25
            Charset         =   129
            Weight          =   700
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         Height          =   315
         Left            =   10080
         TabIndex        =   204
         Top             =   240
         Width           =   2655
      End
      Begin VB.TextBox TextFwDir 
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
         Left            =   3120
         TabIndex        =   201
         Text            =   "C:\\NICEVCAT\\NICE_TCP_V0006_220812.bin"
         Top             =   240
         Width           =   6735
      End
      Begin VB.TextBox TextReaderType 
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
         Left            =   1080
         TabIndex        =   200
         Text            =   "5"
         Top             =   240
         Width           =   495
      End
      Begin VB.Label Label87 
         AutoSize        =   -1  'True
         Caption         =   "펌웨어 파일 경로"
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
         Left            =   1680
         TabIndex        =   203
         Top             =   300
         Width           =   1275
      End
      Begin VB.Label Label86 
         AutoSize        =   -1  'True
         Caption         =   "리더기유형"
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
         Left            =   120
         TabIndex        =   202
         Top             =   300
         Width           =   825
      End
   End
   Begin VB.Frame Frame8 
      Caption         =   "행안부 운전면허 응답DATA"
      BeginProperty Font 
         Name            =   "굴림"
         Size            =   8.25
         Charset         =   129
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   1455
      Left            =   240
      TabIndex        =   176
      Top             =   9240
      Width           =   6255
      Begin VB.TextBox RecvMsg 
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
         Left            =   4560
         TabIndex        =   187
         Top             =   600
         Width           =   1485
      End
      Begin VB.TextBox RecvCode 
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
         Left            =   2880
         TabIndex        =   185
         Top             =   600
         Width           =   645
      End
      Begin VB.TextBox RecvTrx 
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
         Left            =   840
         TabIndex        =   183
         Top             =   600
         Width           =   1245
      End
      Begin VB.TextBox RecvFiller2 
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
         Left            =   2880
         TabIndex        =   179
         Top             =   1020
         Width           =   3200
      End
      Begin VB.TextBox RecvFiller1 
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
         Left            =   840
         TabIndex        =   178
         Top             =   1020
         Width           =   1245
      End
      Begin VB.TextBox RecvQR 
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
         Left            =   840
         TabIndex        =   177
         Top             =   240
         Width           =   5295
      End
      Begin VB.Label Label80 
         Caption         =   "결과메시지"
         BeginProperty Font 
            Name            =   "굴림"
            Size            =   8.25
            Charset         =   129
            Weight          =   400
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         Height          =   255
         Left            =   3600
         TabIndex        =   188
         Top             =   660
         Width           =   975
      End
      Begin VB.Label Label79 
         Caption         =   "결과코드"
         BeginProperty Font 
            Name            =   "굴림"
            Size            =   8.25
            Charset         =   129
            Weight          =   400
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         Height          =   255
         Left            =   2160
         TabIndex        =   186
         Top             =   660
         Width           =   735
      End
      Begin VB.Label Label73 
         Caption         =   "TRX코드"
         BeginProperty Font 
            Name            =   "굴림"
            Size            =   8.25
            Charset         =   129
            Weight          =   400
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         Height          =   255
         Left            =   120
         TabIndex        =   184
         Top             =   660
         Width           =   855
      End
      Begin VB.Label Label78 
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
         Left            =   2160
         TabIndex        =   182
         Top             =   1080
         Width           =   495
      End
      Begin VB.Label Label77 
         Caption         =   "Filler1"
         BeginProperty Font 
            Name            =   "굴림"
            Size            =   8.25
            Charset         =   129
            Weight          =   400
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         Height          =   255
         Left            =   120
         TabIndex        =   181
         Top             =   1080
         Width           =   615
      End
      Begin VB.Label Label76 
         Caption         =   "QR"
         BeginProperty Font 
            Name            =   "굴림"
            Size            =   8.25
            Charset         =   129
            Weight          =   400
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         Height          =   255
         Left            =   120
         TabIndex        =   180
         Top             =   240
         Width           =   615
      End
   End
   Begin VB.Frame Frame7 
      Caption         =   "행안부 운전면허 요청DATA"
      BeginProperty Font 
         Name            =   "굴림"
         Size            =   8.25
         Charset         =   129
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   1095
      Left            =   240
      TabIndex        =   167
      Top             =   8040
      Width           =   6255
      Begin VB.TextBox Text_Num 
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
         Left            =   1080
         TabIndex        =   174
         Text            =   "N001"
         Top             =   240
         Width           =   735
      End
      Begin VB.TextBox Text_QR 
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
         Left            =   2400
         TabIndex        =   170
         Text            =   $"Form1.frx":0000
         Top             =   240
         Width           =   3735
      End
      Begin VB.TextBox Text_Filler1 
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
         Left            =   1080
         TabIndex        =   169
         Top             =   600
         Width           =   1725
      End
      Begin VB.TextBox Text_Filler2 
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
         Left            =   3480
         TabIndex        =   168
         Top             =   600
         Width           =   2640
      End
      Begin VB.Label Label71 
         Caption         =   "전문번호"
         BeginProperty Font 
            Name            =   "굴림"
            Size            =   8.25
            Charset         =   129
            Weight          =   400
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         Height          =   255
         Left            =   120
         TabIndex        =   175
         Top             =   300
         Width           =   855
      End
      Begin VB.Label Label72 
         AutoSize        =   -1  'True
         Caption         =   "QR"
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
         Left            =   1920
         TabIndex        =   173
         Top             =   300
         Width           =   255
      End
      Begin VB.Label Label74 
         AutoSize        =   -1  'True
         Caption         =   "Filler1"
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
         Left            =   120
         TabIndex        =   172
         Top             =   640
         Width           =   495
      End
      Begin VB.Label Label75 
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
         Left            =   2880
         TabIndex        =   171
         Top             =   640
         Width           =   495
      End
   End
   Begin VB.Frame Frame3 
      Caption         =   "수표조회 요청DATA"
      BeginProperty Font 
         Name            =   "굴림"
         Size            =   8.25
         Charset         =   129
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   1095
      Left            =   6600
      TabIndex        =   152
      Top             =   8040
      Width           =   6495
      Begin VB.TextBox Billserial 
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
         Left            =   5640
         TabIndex        =   159
         Top             =   660
         Width           =   720
      End
      Begin VB.TextBox billamt 
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
         Left            =   3840
         TabIndex        =   158
         Top             =   660
         Width           =   720
      End
      Begin VB.TextBox billsn 
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
         Left            =   2280
         TabIndex        =   157
         Top             =   660
         Width           =   720
      End
      Begin VB.TextBox Billdt 
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
         Left            =   840
         TabIndex        =   156
         Top             =   660
         Width           =   720
      End
      Begin VB.TextBox Billno 
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
         Left            =   4560
         TabIndex        =   155
         Top             =   300
         Width           =   1800
      End
      Begin VB.ComboBox Billmoney 
         BeginProperty Font 
            Name            =   "굴림"
            Size            =   8.25
            Charset         =   129
            Weight          =   400
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         Height          =   285
         Left            =   2880
         TabIndex        =   154
         Top             =   300
         Width           =   840
      End
      Begin VB.ComboBox Billtp 
         BeginProperty Font 
            Name            =   "굴림"
            Size            =   8.25
            Charset         =   129
            Weight          =   400
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         Height          =   285
         Left            =   1080
         TabIndex        =   153
         Top             =   300
         Width           =   840
      End
      Begin VB.Label Label34 
         AutoSize        =   -1  'True
         Caption         =   "수표권종"
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
         Left            =   2040
         TabIndex        =   166
         Top             =   360
         Width           =   660
      End
      Begin VB.Label Label33 
         AutoSize        =   -1  'True
         Caption         =   "수표종류"
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
         Left            =   240
         TabIndex        =   165
         Top             =   360
         Width           =   660
      End
      Begin VB.Label Label31 
         AutoSize        =   -1  'True
         Caption         =   "계좌일련번호"
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
         Left            =   4600
         TabIndex        =   164
         Top             =   720
         Width           =   990
      End
      Begin VB.Label Label30 
         AutoSize        =   -1  'True
         Caption         =   "수표금액"
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
         Left            =   3120
         TabIndex        =   163
         Top             =   720
         Width           =   660
      End
      Begin VB.Label Label29 
         AutoSize        =   -1  'True
         Caption         =   "주민번호"
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
         Left            =   1560
         TabIndex        =   162
         Top             =   720
         Width           =   660
      End
      Begin VB.Label Label28 
         AutoSize        =   -1  'True
         Caption         =   "발행일"
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
         Left            =   240
         TabIndex        =   161
         Top             =   720
         Width           =   495
      End
      Begin VB.Label Label27 
         AutoSize        =   -1  'True
         Caption         =   "수표번호"
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
         Left            =   3840
         TabIndex        =   160
         Top             =   360
         Width           =   660
      End
   End
   Begin VB.Frame Frame6 
      Caption         =   "NVCAT IP/PORT 설정 (머니플러스 사용시 IP/PORT 변경 필요)"
      BeginProperty Font 
         Name            =   "굴림"
         Size            =   8.25
         Charset         =   129
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   855
      Left            =   6600
      TabIndex        =   146
      Top             =   9240
      Width           =   6495
      Begin VB.CommandButton Command10 
         Caption         =   "IP/PORT 설정(Set_SvrInfo)"
         BeginProperty Font 
            Name            =   "굴림"
            Size            =   8.25
            Charset         =   129
            Weight          =   700
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         Height          =   315
         Left            =   3360
         TabIndex        =   151
         Top             =   360
         Width           =   2775
      End
      Begin VB.TextBox Iptext 
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
         Left            =   480
         TabIndex        =   150
         Text            =   "211.33.136.19"
         Top             =   360
         Width           =   1335
      End
      Begin VB.TextBox porttext 
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
         Left            =   2400
         TabIndex        =   149
         Text            =   "8101"
         Top             =   360
         Width           =   855
      End
      Begin VB.Label Label43 
         AutoSize        =   -1  'True
         Caption         =   "Port"
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
         Left            =   1920
         TabIndex        =   148
         Top             =   420
         Width           =   345
      End
      Begin VB.Label Label67 
         AutoSize        =   -1  'True
         Caption         =   "IP"
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
         Left            =   240
         TabIndex        =   147
         Top             =   420
         Width           =   165
      End
   End
   Begin VB.Frame Frame5 
      Caption         =   "부정취소 사용여부 설정"
      BeginProperty Font 
         Name            =   "굴림"
         Size            =   8.25
         Charset         =   129
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   495
      Left            =   6600
      TabIndex        =   140
      Top             =   10200
      Width           =   6495
      Begin VB.CommandButton Command21 
         Caption         =   "부정취소설정"
         BeginProperty Font 
            Name            =   "굴림"
            Size            =   8.25
            Charset         =   129
            Weight          =   700
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         Height          =   315
         Left            =   5040
         TabIndex        =   145
         Top             =   160
         Width           =   1335
      End
      Begin VB.TextBox CustomCnl 
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
         Left            =   4560
         TabIndex        =   144
         Text            =   "N"
         Top             =   180
         Width           =   375
      End
      Begin VB.TextBox NiceDownYN 
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
         Left            =   2280
         TabIndex        =   143
         Text            =   "T"
         Top             =   180
         Width           =   375
      End
      Begin VB.Label Label70 
         AutoSize        =   -1  'True
         Caption         =   "부정취소 미사용시 ""Y"""
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
         Left            =   2760
         TabIndex        =   142
         Top             =   240
         Width           =   1710
      End
      Begin VB.Label Label69 
         AutoSize        =   -1  'True
         Caption         =   "가맹점다운로드 테스트여부"
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
         Left            =   120
         TabIndex        =   141
         Top             =   240
         Width           =   2040
      End
   End
   Begin VB.CommandButton Command26 
      Caption         =   "CHK_CARDIN_TIT(TIT 상태체크)"
      BeginProperty Font 
         Name            =   "굴림"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   435
      Left            =   13200
      TabIndex        =   139
      Top             =   8280
      Width           =   2499
   End
   Begin VB.CommandButton Command25 
      Caption         =   "REQ_BALANCE (RF 잔액조회)"
      BeginProperty Font 
         Name            =   "굴림"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   315
      Left            =   13200
      TabIndex        =   138
      Top             =   3360
      Width           =   2499
   End
   Begin VB.CommandButton Command24 
      Caption         =   "REQ_SELECTBTN(PAD)"
      BeginProperty Font 
         Name            =   "굴림"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   315
      Left            =   13200
      TabIndex        =   137
      Top             =   7920
      Width           =   2499
   End
   Begin VB.CommandButton Command23 
      Caption         =   "REQ_SELECTBTN(터치)"
      BeginProperty Font 
         Name            =   "굴림"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   315
      Left            =   13200
      TabIndex        =   136
      Top             =   4200
      Width           =   2499
   End
   Begin VB.CommandButton Command22 
      Caption         =   "REQ_TITLOCK(TDR 수동 LOCK)"
      BeginProperty Font 
         Name            =   "굴림"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   435
      Left            =   13200
      TabIndex        =   135
      Top             =   6600
      Width           =   2499
   End
   Begin VB.CommandButton Command20 
      Caption         =   "GetMac(Mac 주소 얻기)"
      BeginProperty Font 
         Name            =   "굴림"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   315
      Left            =   13200
      TabIndex        =   134
      Top             =   7560
      Width           =   2499
   End
   Begin VB.CommandButton Command18 
      Caption         =   "REQ_CASHNO(고객식별번호 요청)"
      BeginProperty Font 
         Name            =   "굴림"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   435
      Left            =   13200
      TabIndex        =   133
      Top             =   3720
      Width           =   2499
   End
   Begin VB.CommandButton Command17 
      Caption         =   "NVCATSHUTDOWN(NVCAT 강제종료)"
      BeginProperty Font 
         Name            =   "굴림"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   435
      Left            =   13200
      TabIndex        =   132
      Top             =   2400
      Width           =   2499
   End
   Begin VB.CommandButton Command16 
      Caption         =   "CHK_CASHIC2 (현금IC카드여부확인)"
      BeginProperty Font 
         Name            =   "굴림"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   435
      Left            =   13200
      TabIndex        =   131
      Top             =   7080
      Width           =   2499
   End
   Begin VB.CommandButton Command15 
      Caption         =   "REQ_BARCODE (바코드(QR)리딩)"
      BeginProperty Font 
         Name            =   "굴림"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   435
      Left            =   13200
      TabIndex        =   130
      Top             =   1920
      Width           =   2499
   End
   Begin VB.CommandButton Command14 
      Caption         =   "CHK_CARDIN_MP (멀티패드 IC 카드 확인)"
      BeginProperty Font 
         Name            =   "굴림"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   435
      Left            =   13200
      TabIndex        =   129
      Top             =   6120
      Width           =   2499
   End
   Begin VB.CommandButton Command13 
      Caption         =   "CHK_CASHIC_MP(멀티패드 현금IC카드여부확인)"
      BeginProperty Font 
         Name            =   "굴림"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   435
      Left            =   13200
      TabIndex        =   128
      Top             =   5640
      Width           =   2499
   End
   Begin VB.CommandButton Command12 
      Caption         =   "CHK_CARDIN (TIT카드삽입여부확인)"
      BeginProperty Font 
         Name            =   "굴림"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   435
      Left            =   13200
      TabIndex        =   113
      Top             =   600
      Width           =   2499
   End
   Begin VB.CommandButton Command11 
      Caption         =   "CHK_MEMBERSHIP (멤버쉽카드번호조회)"
      BeginProperty Font 
         Name            =   "굴림"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   435
      Left            =   13200
      TabIndex        =   110
      Top             =   9240
      Width           =   2499
   End
   Begin VB.CommandButton Command9 
      Caption         =   "TIT(TCM,TTM)리더기 카드 수동 배출"
      BeginProperty Font 
         Name            =   "굴림"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   435
      Left            =   13200
      TabIndex        =   109
      Top             =   2880
      Width           =   2499
   End
   Begin VB.CommandButton Command8 
      Caption         =   "CHK_CASHIC (현금IC카드여부확인)"
      BeginProperty Font 
         Name            =   "굴림"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   435
      Left            =   13200
      TabIndex        =   100
      Top             =   8760
      Width           =   2499
   End
   Begin VB.OptionButton Option4 
      Caption         =   "화면입력"
      BeginProperty Font 
         Name            =   "굴림"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   180
      Left            =   480
      TabIndex        =   99
      Top             =   2040
      Width           =   2055
   End
   Begin VB.TextBox RecvData 
      BeginProperty Font 
         Name            =   "굴림"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   375
      Left            =   2160
      MultiLine       =   -1  'True
      ScrollBars      =   2  '수직
      TabIndex        =   68
      Top             =   3840
      Width           =   10935
   End
   Begin VB.CommandButton Command5 
      Caption         =   "GET_APPR (직전승인내역조회)"
      BeginProperty Font 
         Name            =   "굴림"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   435
      Left            =   13200
      TabIndex        =   67
      Top             =   1080
      Width           =   2499
   End
   Begin VB.CommandButton Command7 
      Caption         =   "CHK_CARDBIN (카드BIN요청)"
      BeginProperty Font 
         Name            =   "굴림"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   315
      Left            =   13200
      TabIndex        =   66
      Top             =   240
      Width           =   2499
   End
   Begin VB.OptionButton Option3 
      Caption         =   "현금영수증 카드거래"
      BeginProperty Font 
         Name            =   "굴림"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   255
      Left            =   480
      TabIndex        =   65
      Top             =   1740
      Value           =   -1  'True
      Width           =   2175
   End
   Begin VB.OptionButton Option2 
      Caption         =   "현금영수증 식별번호 입력 거래"
      BeginProperty Font 
         Name            =   "굴림"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   375
      Left            =   480
      TabIndex        =   64
      Top             =   1380
      Width           =   3135
   End
   Begin VB.OptionButton Option1 
      Caption         =   "현금영수증 Keyin거래"
      BeginProperty Font 
         Name            =   "굴림"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   255
      Left            =   480
      TabIndex        =   63
      Top             =   1140
      Width           =   2295
   End
   Begin VB.TextBox Text18 
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
      Left            =   14640
      TabIndex        =   58
      Text            =   "5"
      Top             =   5000
      Width           =   975
   End
   Begin VB.CommandButton Command4 
      Caption         =   "READER_RESET"
      BeginProperty Font 
         Name            =   "굴림"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   315
      Left            =   13200
      TabIndex        =   57
      Top             =   5280
      Width           =   2499
   End
   Begin VB.CommandButton Command3 
      Caption         =   "RESTART (NVCAT재시작)"
      BeginProperty Font 
         Name            =   "굴림"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   315
      Left            =   13200
      TabIndex        =   56
      Top             =   1560
      Width           =   2499
   End
   Begin VB.TextBox TextRecv 
      BeginProperty Font 
         Name            =   "굴림"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   285
      Left            =   1080
      MultiLine       =   -1  'True
      TabIndex        =   55
      Top             =   3480
      Width           =   10695
   End
   Begin VB.CommandButton Command2 
      Caption         =   "NICEVCAT"
      BeginProperty Font 
         Name            =   "굴림"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   615
      Left            =   11880
      TabIndex        =   54
      Top             =   3120
      Width           =   1215
   End
   Begin VB.TextBox TextData 
      BeginProperty Font 
         Name            =   "굴림"
         Size            =   8.25
         Charset         =   129
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   285
      Left            =   1080
      MultiLine       =   -1  'True
      TabIndex        =   53
      Top             =   3120
      Width           =   10695
   End
   Begin VB.Frame Frame2 
      Caption         =   " 승인 응답 DATA "
      BeginProperty Font 
         Name            =   "굴림"
         Size            =   8.25
         Charset         =   129
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   3615
      Left            =   240
      TabIndex        =   16
      Top             =   4320
      Width           =   12855
      Begin VB.TextBox Text23 
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
         Left            =   3840
         TabIndex        =   126
         Top             =   3200
         Width           =   1695
      End
      Begin VB.TextBox Text22 
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
         Left            =   1200
         TabIndex        =   107
         Top             =   3200
         Width           =   1695
      End
      Begin VB.TextBox Text21 
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
         Left            =   4800
         TabIndex        =   105
         Top             =   2820
         Width           =   800
      End
      Begin VB.TextBox Text20 
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
         Left            =   3000
         TabIndex        =   103
         Top             =   2820
         Width           =   800
      End
      Begin VB.TextBox Text19 
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
         Left            =   1200
         TabIndex        =   101
         Top             =   2820
         Width           =   800
      End
      Begin VB.TextBox Text_015 
         Height          =   312
         Left            =   7200
         TabIndex        =   98
         Top             =   2100
         Width           =   5475
      End
      Begin VB.TextBox Text_014 
         Height          =   312
         Left            =   11760
         TabIndex        =   97
         Top             =   1740
         Width           =   1000
      End
      Begin VB.TextBox Text_013 
         Height          =   312
         Left            =   9300
         TabIndex        =   96
         Top             =   1740
         Width           =   1000
      End
      Begin VB.TextBox Text_012 
         Height          =   312
         Left            =   7200
         TabIndex        =   95
         Text            =   " "
         Top             =   1740
         Width           =   1000
      End
      Begin VB.TextBox Text_011 
         Height          =   312
         Left            =   9960
         TabIndex        =   94
         Top             =   1380
         Width           =   2835
      End
      Begin VB.TextBox Text_010 
         Height          =   312
         Left            =   7200
         TabIndex        =   93
         Top             =   1380
         Width           =   1000
      End
      Begin VB.TextBox Text_009 
         Height          =   312
         Left            =   11760
         TabIndex        =   92
         Top             =   1020
         Width           =   1000
      End
      Begin VB.TextBox Text_008 
         Height          =   312
         Left            =   9300
         TabIndex        =   91
         Top             =   1020
         Width           =   1000
      End
      Begin VB.TextBox Text_007 
         Height          =   312
         Left            =   7200
         TabIndex        =   90
         Top             =   1020
         Width           =   1000
      End
      Begin VB.TextBox Text_006 
         Height          =   312
         Left            =   9300
         TabIndex        =   89
         Top             =   660
         Width           =   1000
      End
      Begin VB.TextBox Text_005 
         Height          =   312
         Left            =   7200
         TabIndex        =   88
         Top             =   660
         Width           =   1000
      End
      Begin VB.TextBox Text_004 
         Height          =   312
         Left            =   11760
         TabIndex        =   87
         Top             =   660
         Width           =   1000
      End
      Begin VB.TextBox Text_003 
         Height          =   312
         Left            =   11760
         TabIndex        =   86
         Top             =   300
         Width           =   1000
      End
      Begin VB.TextBox Text_002 
         Height          =   312
         Left            =   9300
         TabIndex        =   85
         Top             =   300
         Width           =   1000
      End
      Begin VB.TextBox Text_001 
         Height          =   312
         Left            =   7200
         TabIndex        =   84
         Top             =   300
         Width           =   1000
      End
      Begin VB.TextBox Text17 
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
         Left            =   1200
         TabIndex        =   33
         Top             =   2460
         Width           =   4335
      End
      Begin VB.TextBox Text16 
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
         Left            =   4800
         TabIndex        =   32
         Top             =   2100
         Width           =   800
      End
      Begin VB.TextBox Text15 
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
         Left            =   3000
         TabIndex        =   31
         Top             =   2100
         Width           =   800
      End
      Begin VB.TextBox Text14 
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
         Left            =   1200
         TabIndex        =   30
         Top             =   2100
         Width           =   800
      End
      Begin VB.TextBox Text13 
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
         Left            =   3000
         TabIndex        =   29
         Top             =   1740
         Width           =   2535
      End
      Begin VB.TextBox Text12 
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
         Left            =   1200
         TabIndex        =   28
         Top             =   1740
         Width           =   800
      End
      Begin VB.TextBox Text11 
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
         Left            =   3000
         TabIndex        =   27
         Top             =   1380
         Width           =   2535
      End
      Begin VB.TextBox Text10 
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
         Left            =   1200
         TabIndex        =   26
         Top             =   1380
         Width           =   800
      End
      Begin VB.TextBox Text9 
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
         Left            =   4800
         TabIndex        =   25
         Top             =   1020
         Width           =   800
      End
      Begin VB.TextBox Text8 
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
         Left            =   3000
         TabIndex        =   24
         Top             =   1020
         Width           =   800
      End
      Begin VB.TextBox Text7 
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
         Left            =   1200
         TabIndex        =   23
         Top             =   1020
         Width           =   800
      End
      Begin VB.TextBox Text6 
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
         Left            =   4800
         TabIndex        =   22
         Top             =   660
         Width           =   800
      End
      Begin VB.TextBox Text5 
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
         Left            =   3000
         TabIndex        =   21
         Top             =   660
         Width           =   800
      End
      Begin VB.TextBox Text4 
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
         Left            =   1200
         TabIndex        =   20
         Top             =   660
         Width           =   800
      End
      Begin VB.TextBox Text3 
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
         Left            =   4800
         TabIndex        =   19
         Top             =   300
         Width           =   800
      End
      Begin VB.TextBox Text2 
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
         Left            =   3000
         TabIndex        =   18
         Top             =   300
         Width           =   800
      End
      Begin VB.TextBox Text1 
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
         Left            =   1200
         TabIndex        =   17
         Top             =   285
         Width           =   800
      End
      Begin VB.Label Label68 
         AutoSize        =   -1  'True
         Caption         =   "Filler"
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
         Left            =   3000
         TabIndex        =   127
         Top             =   3240
         Width           =   405
      End
      Begin VB.Label Label41 
         AutoSize        =   -1  'True
         Caption         =   "거래일련번호"
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
         Left            =   120
         TabIndex        =   108
         Top             =   3240
         Width           =   990
      End
      Begin VB.Label Label40 
         AutoSize        =   -1  'True
         Caption         =   "전문관리번호"
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
         Left            =   3800
         TabIndex        =   106
         Top             =   2880
         Width           =   990
      End
      Begin VB.Label Label39 
         AutoSize        =   -1  'True
         Caption         =   "카드구분"
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
         Left            =   2085
         TabIndex        =   104
         Top             =   2880
         Width           =   660
      End
      Begin VB.Label Label38 
         AutoSize        =   -1  'True
         Caption         =   "카드BIN"
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
         Left            =   240
         TabIndex        =   102
         Top             =   2880
         Width           =   585
      End
      Begin VB.Label Label47 
         AutoSize        =   -1  'True
         Caption         =   "발급기관대표코드"
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
         Left            =   5800
         TabIndex        =   83
         Top             =   360
         Width           =   1320
      End
      Begin VB.Label Label48 
         AutoSize        =   -1  'True
         Caption         =   "발급기관명"
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
         Left            =   8400
         TabIndex        =   82
         Top             =   360
         Width           =   825
      End
      Begin VB.Label Label49 
         AutoSize        =   -1  'True
         Caption         =   "발급기관점별코드"
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
         Left            =   10365
         TabIndex        =   81
         Top             =   360
         Width           =   1320
      End
      Begin VB.Label Label50 
         AutoSize        =   -1  'True
         Caption         =   "매입기관대표코드"
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
         Left            =   5805
         TabIndex        =   80
         Top             =   720
         Width           =   1320
      End
      Begin VB.Label Label51 
         AutoSize        =   -1  'True
         Caption         =   "매입기관명"
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
         Left            =   8400
         TabIndex        =   79
         Top             =   720
         Width           =   825
      End
      Begin VB.Label Label52 
         AutoSize        =   -1  'True
         Caption         =   "매입기관점별코드"
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
         Left            =   10365
         TabIndex        =   78
         Top             =   720
         Width           =   1320
      End
      Begin VB.Label Label53 
         AutoSize        =   -1  'True
         Caption         =   "수수료율"
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
         Left            =   5805
         TabIndex        =   77
         Top             =   1080
         Width           =   660
      End
      Begin VB.Label Label54 
         AutoSize        =   -1  'True
         Caption         =   "가맹점수수료"
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
         Left            =   8280
         TabIndex        =   76
         Top             =   1080
         Width           =   990
      End
      Begin VB.Label Label55 
         AutoSize        =   -1  'True
         Caption         =   "발급기관 수수료"
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
         Left            =   10365
         TabIndex        =   75
         Top             =   1080
         Width           =   1215
      End
      Begin VB.Label Label56 
         AutoSize        =   -1  'True
         Caption         =   "매입기관 수수료"
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
         Left            =   5805
         TabIndex        =   74
         Top             =   1440
         Width           =   1215
      End
      Begin VB.Label Label57 
         AutoSize        =   -1  'True
         Caption         =   "출력용 출금계좌번호"
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
         Left            =   8280
         TabIndex        =   73
         Top             =   1440
         Width           =   1545
      End
      Begin VB.Label Label58 
         AutoSize        =   -1  'True
         Caption         =   "원장잔액부호"
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
         Left            =   5805
         TabIndex        =   72
         Top             =   1800
         Width           =   990
      End
      Begin VB.Label Label59 
         AutoSize        =   -1  'True
         Caption         =   "원장잔액"
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
         Left            =   8520
         TabIndex        =   71
         Top             =   1800
         Width           =   660
      End
      Begin VB.Label Label60 
         AutoSize        =   -1  'True
         Caption         =   "출금가능금액"
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
         Left            =   10365
         TabIndex        =   70
         Top             =   1800
         Width           =   990
      End
      Begin VB.Label Label61 
         AutoSize        =   -1  'True
         Caption         =   "응답메시지"
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
         Left            =   5805
         TabIndex        =   69
         Top             =   2160
         Width           =   825
      End
      Begin VB.Label Label24 
         AutoSize        =   -1  'True
         Caption         =   "응답메시지"
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
         Left            =   240
         TabIndex        =   50
         Top             =   2520
         Width           =   825
      End
      Begin VB.Label Label23 
         AutoSize        =   -1  'True
         Caption         =   "잔액"
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
         Left            =   4000
         TabIndex        =   49
         Top             =   2160
         Width           =   330
      End
      Begin VB.Label Label22 
         AutoSize        =   -1  'True
         Caption         =   "승인CATID"
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
         Left            =   2085
         TabIndex        =   48
         Top             =   2160
         Width           =   840
      End
      Begin VB.Label Label21 
         AutoSize        =   -1  'True
         Caption         =   "가맹점번호"
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
         Left            =   240
         TabIndex        =   47
         Top             =   2160
         Width           =   825
      End
      Begin VB.Label Label20 
         AutoSize        =   -1  'True
         Caption         =   "매입사명"
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
         Left            =   2085
         TabIndex        =   46
         Top             =   1800
         Width           =   660
      End
      Begin VB.Label Label19 
         AutoSize        =   -1  'True
         Caption         =   "매입사코드"
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
         Left            =   240
         TabIndex        =   45
         Top             =   1800
         Width           =   825
      End
      Begin VB.Label Label18 
         AutoSize        =   -1  'True
         Caption         =   "발급사명"
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
         Left            =   2085
         TabIndex        =   44
         Top             =   1440
         Width           =   660
      End
      Begin VB.Label Label17 
         AutoSize        =   -1  'True
         Caption         =   "발급사코드"
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
         Left            =   240
         TabIndex        =   43
         Top             =   1440
         Width           =   825
      End
      Begin VB.Label Label16 
         AutoSize        =   -1  'True
         Caption         =   "승인일시"
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
         Left            =   4000
         TabIndex        =   42
         Top             =   1080
         Width           =   660
      End
      Begin VB.Label Label15 
         AutoSize        =   -1  'True
         Caption         =   "승인번호"
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
         Left            =   2085
         TabIndex        =   41
         Top             =   1080
         Width           =   660
      End
      Begin VB.Label Label14 
         AutoSize        =   -1  'True
         Caption         =   "할부개월"
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
         Left            =   240
         TabIndex        =   40
         Top             =   1080
         Width           =   660
      End
      Begin VB.Label Label13 
         AutoSize        =   -1  'True
         Caption         =   "봉사료"
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
         Left            =   4000
         TabIndex        =   39
         Top             =   720
         Width           =   495
      End
      Begin VB.Label Label12 
         AutoSize        =   -1  'True
         Caption         =   "부가세"
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
         Left            =   2085
         TabIndex        =   38
         Top             =   720
         Width           =   495
      End
      Begin VB.Label Label11 
         AutoSize        =   -1  'True
         Caption         =   "거래금액"
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
         Left            =   240
         TabIndex        =   37
         Top             =   720
         Width           =   660
      End
      Begin VB.Label Label10 
         AutoSize        =   -1  'True
         Caption         =   "응답코드"
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
         Left            =   4000
         TabIndex        =   36
         Top             =   360
         Width           =   660
      End
      Begin VB.Label Label9 
         AutoSize        =   -1  'True
         Caption         =   "거래유형"
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
         Left            =   2085
         TabIndex        =   35
         Top             =   360
         Width           =   660
      End
      Begin VB.Label Label1 
         AutoSize        =   -1  'True
         Caption         =   "거래구분"
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
         Left            =   240
         TabIndex        =   34
         Top             =   360
         Width           =   660
      End
   End
   Begin VB.Frame Frame1 
      Caption         =   " 승인 요청 DATA "
      BeginProperty Font 
         Name            =   "굴림"
         Size            =   8.25
         Charset         =   129
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   2895
      Left            =   240
      TabIndex        =   0
      Top             =   120
      Width           =   12855
      Begin VB.TextBox ApprPersonno 
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
         Left            =   12240
         TabIndex        =   211
         Top             =   1020
         Width           =   495
      End
      Begin VB.CommandButton Command27 
         Caption         =   "REQ_STOP (카드리딩요청취소)"
         BeginProperty Font 
            Name            =   "굴림"
            Size            =   8.25
            Charset         =   129
            Weight          =   400
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         Height          =   315
         Left            =   7200
         TabIndex        =   205
         Top             =   2400
         Width           =   2775
      End
      Begin VB.TextBox Text_Domain 
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
         Left            =   9960
         TabIndex        =   196
         Top             =   1380
         Width           =   495
      End
      Begin VB.TextBox Text_IP 
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
         Left            =   11640
         TabIndex        =   195
         Top             =   1380
         Width           =   1095
      End
      Begin VB.TextBox Text_MsgText 
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
         Left            =   4800
         TabIndex        =   191
         Top             =   1380
         Width           =   495
      End
      Begin VB.TextBox Text_Kind 
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
         Left            =   6240
         TabIndex        =   190
         Top             =   1380
         Width           =   615
      End
      Begin VB.TextBox Text_UniNum 
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
         Left            =   8160
         TabIndex        =   189
         Top             =   1380
         Width           =   1095
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
         Left            =   4680
         TabIndex        =   123
         Top             =   2400
         Width           =   2415
      End
      Begin VB.TextBox MPBugainfo 
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
         Left            =   8400
         TabIndex        =   121
         Text            =   "NAME:LEE|NO:18102900001|TITLE:TOOTH(0001)|RECVOFFICE : NO(0001)|RECVNAME:KIM|"
         Top             =   2000
         Width           =   4335
      End
      Begin VB.TextBox MPBizcd 
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
         Left            =   6720
         TabIndex        =   119
         Text            =   "MPS"
         Top             =   2000
         Width           =   615
      End
      Begin VB.TextBox MPBugaYN 
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
         Left            =   5160
         TabIndex        =   117
         Text            =   "Y"
         Top             =   2000
         Width           =   495
      End
      Begin VB.TextBox SignData 
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
         Left            =   6360
         TabIndex        =   115
         Top             =   1020
         Width           =   4905
      End
      Begin VB.TextBox Dealgb 
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
         Left            =   12240
         MaxLength       =   2
         TabIndex        =   111
         Text            =   "40"
         Top             =   660
         Width           =   495
      End
      Begin VB.TextBox Textcashno 
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
         Left            =   9120
         TabIndex        =   62
         Top             =   660
         Width           =   2175
      End
      Begin VB.TextBox TCATID 
         BeginProperty Font 
            Name            =   "굴림"
            Size            =   8.25
            Charset         =   129
            Weight          =   400
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         Height          =   315
         Left            =   4680
         TabIndex        =   51
         Top             =   660
         Width           =   855
      End
      Begin VB.CommandButton Command6 
         Caption         =   "전문생성 및 승인요청"
         BeginProperty Font 
            Name            =   "굴림"
            Size            =   8.25
            Charset         =   129
            Weight          =   700
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         Height          =   315
         Left            =   10080
         TabIndex        =   15
         Top             =   2400
         Width           =   2655
      End
      Begin VB.TextBox TextAgreeDate 
         BeginProperty Font 
            Name            =   "굴림"
            Size            =   8.25
            Charset         =   129
            Weight          =   400
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         Height          =   315
         Left            =   11520
         TabIndex        =   13
         Text            =   "YYMMDD"
         Top             =   300
         Width           =   1215
      End
      Begin VB.TextBox TextAgreeNum 
         BeginProperty Font 
            Name            =   "굴림"
            Size            =   8.25
            Charset         =   129
            Weight          =   400
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         Height          =   315
         Left            =   9480
         TabIndex        =   11
         Top             =   300
         Width           =   1215
      End
      Begin VB.ComboBox ComboHalbu 
         BeginProperty Font 
            Name            =   "굴림"
            Size            =   8.25
            Charset         =   129
            Weight          =   400
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         Height          =   285
         Left            =   1080
         TabIndex        =   9
         Top             =   660
         Width           =   2655
      End
      Begin VB.TextBox TextTax 
         BeginProperty Font 
            Name            =   "굴림"
            Size            =   8.25
            Charset         =   129
            Weight          =   400
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         Height          =   315
         Left            =   6240
         TabIndex        =   6
         Text            =   "0"
         Top             =   300
         Width           =   780
      End
      Begin VB.TextBox TextBongsa 
         BeginProperty Font 
            Name            =   "굴림"
            Size            =   8.25
            Charset         =   129
            Weight          =   400
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         Height          =   315
         Left            =   7800
         TabIndex        =   5
         Text            =   "0"
         Top             =   300
         Width           =   780
      End
      Begin VB.TextBox TextMoney 
         BeginProperty Font 
            Name            =   "굴림"
            Size            =   8.25
            Charset         =   129
            Weight          =   400
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         Height          =   315
         Left            =   4680
         TabIndex        =   3
         Text            =   "1004"
         Top             =   300
         Width           =   900
      End
      Begin VB.ComboBox ComboDeal 
         BeginProperty Font 
            Name            =   "굴림"
            Size            =   8.25
            Charset         =   129
            Weight          =   400
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         Height          =   285
         Left            =   1080
         TabIndex        =   1
         Top             =   300
         Width           =   2655
      End
      Begin VB.Label Label26 
         AutoSize        =   -1  'True
         Caption         =   "주민번호"
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
         Left            =   11400
         TabIndex        =   212
         Top             =   1080
         Width           =   660
      End
      Begin VB.Label Label85 
         AutoSize        =   -1  'True
         Caption         =   "도메인"
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
         Left            =   9360
         TabIndex        =   198
         Top             =   1440
         Width           =   495
      End
      Begin VB.Label Label84 
         AutoSize        =   -1  'True
         Caption         =   "IP ADDRESS"
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
         Left            =   10560
         TabIndex        =   197
         Top             =   1440
         Width           =   1050
      End
      Begin VB.Label Label83 
         AutoSize        =   -1  'True
         Caption         =   "전문TEXT"
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
         Left            =   3960
         TabIndex        =   194
         Top             =   1440
         Width           =   765
      End
      Begin VB.Label Label82 
         AutoSize        =   -1  'True
         Caption         =   "기종구분"
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
         Left            =   5400
         TabIndex        =   193
         Top             =   1440
         Width           =   660
      End
      Begin VB.Label Label81 
         AutoSize        =   -1  'True
         Caption         =   "원거래고유번호"
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
         Left            =   6960
         TabIndex        =   192
         Top             =   1440
         Width           =   1155
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
         Left            =   3960
         TabIndex        =   124
         Top             =   2400
         Width           =   495
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
         Left            =   7560
         TabIndex        =   122
         Top             =   2040
         Width           =   660
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
         Left            =   5760
         TabIndex        =   120
         Top             =   2040
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
         Left            =   3960
         TabIndex        =   118
         Top             =   2040
         Width           =   990
      End
      Begin VB.Label Label46 
         AutoSize        =   -1  'True
         Caption         =   "머니플러스 사용시 아래 정보 입력 (부가정보여부, 가맹점코드, 부가정보, Filler2)"
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
         Left            =   3960
         TabIndex        =   116
         Top             =   1760
         Width           =   6750
      End
      Begin VB.Label Label45 
         AutoSize        =   -1  'True
         Caption         =   "서명데이터(암호화가맹점정보)"
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
         Left            =   3960
         TabIndex        =   114
         Top             =   1080
         Width           =   2265
      End
      Begin VB.Label Label44 
         AutoSize        =   -1  'True
         Caption         =   "거래유형"
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
         Left            =   11400
         TabIndex        =   112
         Top             =   720
         Width           =   660
      End
      Begin VB.Label Label37 
         AutoSize        =   -1  'True
         Caption         =   "현금식별번호(토큰/DCC POS 2TR 환율정보)"
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
         Left            =   5640
         TabIndex        =   61
         Top             =   720
         Width           =   3405
      End
      Begin VB.Label Label25 
         AutoSize        =   -1  'True
         Caption         =   "CATID"
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
         Left            =   3960
         TabIndex        =   52
         Top             =   720
         Width           =   510
      End
      Begin VB.Label Label4 
         AutoSize        =   -1  'True
         Caption         =   "승인날짜"
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
         Left            =   10800
         TabIndex        =   14
         Top             =   360
         Width           =   660
      End
      Begin VB.Label Label3 
         AutoSize        =   -1  'True
         Caption         =   "승인번호"
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
         Left            =   8760
         TabIndex        =   12
         Top             =   360
         Width           =   660
      End
      Begin VB.Label Label6 
         Alignment       =   1  '오른쪽 맞춤
         AutoSize        =   -1  'True
         Caption         =   "할부"
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
         Left            =   480
         TabIndex        =   10
         Top             =   720
         Width           =   330
      End
      Begin VB.Label Label7 
         AutoSize        =   -1  'True
         Caption         =   "부가세"
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
         Left            =   5640
         TabIndex        =   8
         Top             =   360
         Width           =   495
      End
      Begin VB.Label Label8 
         AutoSize        =   -1  'True
         Caption         =   "봉사료"
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
         Left            =   7200
         TabIndex        =   7
         Top             =   360
         Width           =   495
      End
      Begin VB.Label Label2 
         AutoSize        =   -1  'True
         Caption         =   "거래금액"
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
         Left            =   3960
         TabIndex        =   4
         Top             =   360
         Width           =   660
      End
      Begin VB.Label Label5 
         AutoSize        =   -1  'True
         Caption         =   "거래종류"
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
         Left            =   240
         TabIndex        =   2
         Top             =   360
         Width           =   660
      End
   End
   Begin VB.Label Label32 
      AutoSize        =   -1  'True
      Caption         =   "Reset 대기시간"
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
      Left            =   13320
      TabIndex        =   207
      Top             =   5040
      Width           =   1215
   End
   Begin VB.Label Label66 
      AutoSize        =   -1  'True
      Caption         =   "응답전문 FULLDATA"
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
      Left            =   240
      TabIndex        =   125
      Top             =   3960
      Width           =   1785
   End
   Begin VB.Label Label36 
      AutoSize        =   -1  'True
      Caption         =   "응답전문"
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
      Left            =   240
      TabIndex        =   60
      Top             =   3560
      Width           =   720
   End
   Begin VB.Label Label35 
      AutoSize        =   -1  'True
      Caption         =   "요청전문"
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
      Left            =   240
      TabIndex        =   59
      Top             =   3200
      Width           =   720
   End
End
Attribute VB_Name = "Form1"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Private Declare Function NICEVCAT Lib "C:\NICEVCAT\NVCAT.dll" (ByVal send_data As String, ByRef recv_data As Byte) As Long
Private Declare Function REQ_STOP Lib "C:\NICEVCAT\NVCAT.dll" () As Long
Private Declare Function RESTART Lib "C:\NICEVCAT\NVCAT.dll" () As Long
Private Declare Function READER_RESET Lib "C:\NICEVCAT\NVCAT.dll" (ByVal time As String) As Long
Private Declare Function GET_APPR Lib "C:\NICEVCAT\NVCAT.dll" (ByRef recv_data As Byte) As Long
Private Declare Function CHK_CARDBIN Lib "C:\NICEVCAT\NVCAT.dll" (ByRef recv_data As Byte) As Long
Private Declare Function CHK_CASHIC Lib "C:\NICEVCAT\NVCAT.dll" () As Long
Private Declare Function CHK_CASHIC_MP Lib "C:\NICEVCAT\NVCAT.dll" () As Long
Private Declare Function Set_SvrInfo Lib "C:\NICEVCAT\NVCAT.dll" (ByVal ip As String, ByVal port As String) As Long
Private Declare Function Get_SvrInfo Lib "C:\NICEVCAT\NICEPOSICV105.dll" (ByRef ip As Byte, ByRef port As Byte) As Long
Private Declare Function CHK_MEMBERSHIP Lib "C:\NICEVCAT\NVCAT.dll" (ByRef recv_data As Byte) As Long
Private Declare Function CHK_CARDIN Lib "C:\NICEVCAT\NVCAT.dll" () As Long
Private Declare Function ReqStop Lib "C:\NICEVCAT\NICEPOSICV105.dll" () As Long
Private Declare Function CHK_CARDIN_MP Lib "C:\NICEVCAT\NVCAT.dll" (ByRef recv_data As Byte) As Long
Private Declare Function REQ_BARCODE Lib "C:\NICEVCAT\NVCAT.dll" (ByVal hwtype As String, ByRef recv_data As Byte) As Long
Private Declare Function CHK_CASHIC2 Lib "C:\NICEVCAT\NVCAT.dll" () As Long
Private Declare Function NVCATSHUTDOWN Lib "C:\NICEVCAT\NVCAT.dll" () As Long
Private Declare Function REQ_CASHNO Lib "C:\NICEVCAT\NVCAT.dll" (ByRef recv_data As Byte) As Long
Private Declare Function GetMac Lib "C:\NICEVCAT\NVCAT.dll" (ByRef Mac As Byte) As Long
Private Declare Function SetCnlDisableYN Lib "C:\NICEVCAT\NVCAT.dll" (ByVal NiceDownYN As String, ByVal CustomCnlYN As String) As Long
Private Declare Function REQ_TITLOCK Lib "C:\NICEVCAT\NVCAT.dll" () As Long
Private Declare Function REQ_SELECTBTN Lib "C:\NICEVCAT\NVCAT.dll" (ByVal reqtype As String, ByVal senddata As String, ByRef RecvData As Byte) As Long
Private Declare Function REQ_BALANCE Lib "C:\NICEVCAT\NVCAT.dll" (ByVal hwtype As String, ByRef recv_data As Byte) As Long
Private Declare Function CHK_CARDIN_TIT Lib "C:\NICEVCAT\NVCAT.dll" () As Long
Private Declare Function REQ_SIGNDATA Lib "C:\NICEVCAT\NVCAT.dll" (ByRef recv_data As Byte) As Long
Private Declare Function REQ_FW_UPDATE Lib "C:\NICEVCAT\NVCAT.dll" (ByVal readertype As Long, ByVal fwfilepath As String) As Long
Private Declare Function GetDecSignData Lib "C:\NICEVCAT\NVCAT.dll" (ByVal signtype As Long, ByVal Indata As String, ByRef Outputdata As Byte) As Long
Private Declare Function REQ_CASHIC_AL Lib "C:\NICEVCAT\NVCAT.dll" (ByVal sReaderType As String, ByRef bRecvData As Byte) As Long
Private Declare Function CHK_CASHIC_CARDBIN Lib "C:\NICEVCAT\NVCAT.dll" (ByVal sCardBin As String, ByRef bRecvData As Byte) As Long
Private Declare Function NICEVCATMULTI Lib "C:\NICEVCAT\NVCAT.dll" (ByVal send_data As String, ByRef recv_data As Byte) As Long

Dim FS As String
Dim US As String

Private Sub ComboDeal_Click()
    
    Select Case (ComboDeal.ListIndex)
    Case 43 '컵보증금
        Text_UniNum = "CD0000000300"
    End Select
    
    
    Select Case (ComboDeal.ListIndex)
    Case 0, 1, 3, 5, 8, 10, 21, 23, 25, 27, 30, 31, 33, 34
        TextAgreeNum.Enabled = False
        TextAgreeNum.BackColor = RGB(120, 120, 120)
        TextAgreeDate.Enabled = False
        TextAgreeDate.BackColor = RGB(120, 120, 120)
    Case 2, 4, 6, 9, 11, 12, 13, 14, 15, 16, 22, 20, 24, 26, 28, 32, 35, 40
        TextAgreeNum.Enabled = True
        TextAgreeNum.BackColor = RGB(255, 255, 255)
        TextAgreeDate.Enabled = True
        TextAgreeDate.BackColor = RGB(255, 255, 255)
    End Select
    
    
    Select Case (ComboDeal.ListIndex)
    Case 0, 1, 2, 13, 14, 27
        Label6.Caption = "할부"
        ComboHalbu.Clear
        ComboHalbu.AddItem ("0개월")
        ComboHalbu.AddItem ("1개월")
        ComboHalbu.AddItem ("2개월")
        ComboHalbu.AddItem ("3개월")
        ComboHalbu.AddItem ("4개월")
        ComboHalbu.AddItem ("5개월")
        ComboHalbu.AddItem ("6개월")
        ComboHalbu.AddItem ("7개월")
        ComboHalbu.AddItem ("8개월")
        ComboHalbu.AddItem ("9개월")
        ComboHalbu.AddItem ("10개월")
        ComboHalbu.AddItem ("11개월")
        ComboHalbu.AddItem ("12개월")
        ComboHalbu.ListIndex = 0
    Case 3, 4, 15
        Label6.Caption = "발급구분"
        ComboHalbu.Clear
        ComboHalbu.AddItem ("1소비자")
        ComboHalbu.AddItem ("2사업자")
        ComboHalbu.AddItem ("3자진발급")
        ComboHalbu.ListIndex = 0
    End Select
    
    If ComboDeal.ListIndex = 19 Or ComboDeal.ListIndex = 20 Then
        Dealgb.Text = "70"
    ElseIf ComboDeal.ListIndex = 21 Or ComboDeal.ListIndex = 22 Then
        Dealgb.Text = "40"
        Label7.Caption = "적립구분"
        Label8.Caption = "포인트구분"
        Label37.Caption = "비밀번호"
    ElseIf ComboDeal.ListIndex = 27 Then
        Dealgb.Text = "S1"
    ElseIf ComboDeal.ListIndex = 34 Or ComboDeal.ListIndex = 35 Then
        Label7.Caption = "적립구분"
        Label8.Caption = "포인트구분"
        Label37.Caption = "Filler2"
    ElseIf ComboDeal.ListIndex = 44 Then
        Dealgb.Text = "S2"
    ElseIf ComboDeal.ListIndex = 30 Then
        Dealgb.Text = "N1"
    ElseIf ComboDeal.ListIndex = 31 Or ComboDeal.ListIndex = 32 Then
        Dealgb.Text = "N2"
    ElseIf ComboDeal.ListIndex = 33 Then
        Dealgb.Text = "N3"
    Else
        Label7.Caption = "부가세"
        Label8.Caption = "봉사료"
        Label37.Caption = "현금식별번호(토큰/DCC POS 2TR 환율정보)"
    End If
        
End Sub

Private Sub Command1_Click()
    Dim ret As Long
    ret = REQ_FW_UPDATE(TextReaderType.Text, TextFwDir.Text)
    MsgBox (ret)
End Sub

Private Sub Command10_Click()
    Dim ret As Long
    
    ret = Set_SvrInfo(Iptext.Text, porttext)
    MsgBox (ret)
End Sub

Private Sub Command11_Click()
    Dim ret As Long
    Dim bReceData(1024) As Byte
    ret = CHK_MEMBERSHIP(bReceData(0))
    
    If ret > 0 Then
       MsgBox (StrConv(bReceData, vbUnicode))
    Else
        MsgBox (ret)
       MsgBox ("실패")
    End If
End Sub



Private Sub Command12_Click()
    Dim ret As Long
    ret = CHK_CARDIN()
    
    MsgBox (ret)
End Sub

Private Sub Command13_Click()
    Dim ret As Long
    ret = CHK_CASHIC_MP()
    MsgBox (ret)
End Sub

Private Sub Command14_Click()
    Dim ret As Long
    
    Dim bRecvData(3000) As Byte
    ret = CHK_CARDIN_MP(bRecvData(0))
    
    MsgBox (ret)
    
    If ret <> 1 Then
        MsgBox ("리턴값 확인하세요")
        Exit Sub
    End If
    
    MsgBox ("응답데이터 : " + StrConv(bRecvData, vbUnicode))
End Sub

Private Sub Command15_Click()
    Dim ret As Long
    
    Dim bRecvData(3000) As Byte
    ret = REQ_BARCODE("2", bRecvData(0))
    
    MsgBox (ret)
    
    If ret <> 1 Then
        MsgBox ("리턴값 확인하세요")
        Exit Sub
    End If
    
    MsgBox ("응답데이터 : " + StrConv(bRecvData, vbUnicode))
    RecvData.Text = StrConv(bRecvData, vbUnicode)
End Sub

Private Sub Command16_Click()
    Dim ret As Long
    ret = CHK_CASHIC2()
    MsgBox (ret)
End Sub

Private Sub Command17_Click()
    Dim ret As Long
    ret = NVCATSHUTDOWN()
End Sub

Private Sub Command18_Click()
    Dim ret As Long
    
    Dim bRecvData(3000) As Byte
    ret = REQ_CASHNO(bRecvData(0))
    
    MsgBox (ret)
    
    If ret <> 1 Then
        MsgBox ("리턴값 확인하세요")
        Exit Sub
    End If
    
    MsgBox ("고객식별번호 : " + StrConv(bRecvData, vbUnicode))
    RecvData.Text = StrConv(bRecvData, vbUnicode)
End Sub

Private Sub Command19_Click()
    Dim signtype As Long
    Dim Indata As String
    Dim Outputdata(4096) As Byte
    Dim ret As Long
    
    signtype = 2

    ret = GetDecSignData(signtype, "SignDataBmp.bmp", Outputdata(0))
    
    RecvData.Text = StrConv(Outputdata, vbUnicode)
End Sub

Private Sub Command2_Click()

    FS = Chr$(&H1C)
    
    Dim send_data As String
    Dim recv_data As String
    Dim bRcvData(1024) As Byte
    
    TextRecv.Text = ""
    send_data = TextData.Text
        
    If Len(send_data) = 0 Then
        MsgBox ("요청 전문을 확인하세요")
        Exit Sub
    End If
    
    Dim m As Long
    m = NICEVCAT(send_data, bRcvData(0))
    MsgBox (m)  '리턴값 처리 꼭 해주세요!!!!
    
    If m <> 1 Then
        Exit Sub
    End If
    
  recv_data = StrConv(bRcvData, vbUnicode)
  TextRecv.Text = recv_data
    
    
End Sub

Private Sub Command20_Click()
    Dim ret As Long
    
    Dim Mac(3000) As Byte
    ret = GetMac(Mac(0))
    
    If ret <> 1 Then
        MsgBox ("리턴값 확인하세요")
        Exit Sub
    End If
    
    MsgBox ("MAC 값 : " + StrConv(Mac, vbUnicode))
End Sub

Private Sub Command21_Click()
    MsgBox ("가맹점다운로드 테스트시 T / 운영시 1(Default)")
    MsgBox ("부정취소 미사용시 Y / 사용시 N(Default)")
    Dim ret As Long
    ret = SetCnlDisableYN(NiceDownYN.Text, CustomCnl.Text)
    MsgBox (ret)
End Sub

Private Sub Command22_Click()
    Dim ret As Long
    
    ret = REQ_TITLOCK()
    
    MsgBox (ret)
End Sub

Private Sub Command23_Click()
    Dim ret As Long
    
    Dim bRecvData(3000) As Byte
    ret = REQ_SELECTBTN("2", "현금 IC거래를 진행하시겠습니까?           ", bRecvData(0))
    
    MsgBox (ret)
    
    If ret <> 1 Then
        MsgBox ("리턴값 확인하세요")
        Exit Sub
    End If
    
    MsgBox ("응답데이터 : " + StrConv(bRecvData, vbUnicode))
    RecvData.Text = StrConv(bRecvData, vbUnicode)
End Sub

Private Sub Command24_Click()
    Dim ret As Long
    
    Dim bRecvData(3000) As Byte
    ret = REQ_SELECTBTN("1", "현금 IC거래를 진행하시겠습니까?           ", bRecvData(0))
    
    MsgBox (ret)
    
    If ret <> 1 Then
        MsgBox ("리턴값 확인하세요")
        Exit Sub
    End If
    
    MsgBox ("응답데이터 : " + StrConv(bRecvData, vbUnicode))
    RecvData.Text = StrConv(bRecvData, vbUnicode)
End Sub

Private Sub Command25_Click()
    Dim ret As Long
    
    Dim bRecvData(3000) As Byte
    ret = REQ_BALANCE("1", bRecvData(0))
    
    MsgBox (ret)
    
    If ret <> 1 Then
        MsgBox ("리턴값 확인하세요")
        Exit Sub
    End If
    
    MsgBox ("응답데이터 : " + StrConv(bRecvData, vbUnicode))
    RecvData.Text = StrConv(bRecvData, vbUnicode)
End Sub

Private Sub Command26_Click()
Dim ret As Long
    ret = CHK_CARDIN_TIT()
    MsgBox (ret)
End Sub

Private Sub Command27_Click()
    Dim ret As Long
    ret = REQ_STOP()
End Sub

Private Sub Command28_Click()
   Dim m As Long
    Dim bReceData(1024) As Byte
    m = REQ_SIGNDATA(bReceData(0))
    MsgBox (m)  '리턴값 처리 꼭 해주세요!!!!
    
    If m <> 1 Then
        Exit Sub
    End If
    
    recv_data = StrConv(bReceData, vbUnicode)
    RecvData.Text = recv_data
End Sub

Private Sub Command29_Click()
    Dim ret As Long
    Dim bRecvData(1024) As Byte
    
    ret = REQ_CASHIC_AL("1", bRecvData(0))
    
    MsgBox (ret)
    MsgBox (StrConv(bRecvData, vbUnicode))
End Sub

Private Sub Command3_Click()
    Dim ret As Long
    
    ret = RESTART()
End Sub

Private Sub Command30_Click()
    Dim ret As Long
    Dim sCardBin As String
    Dim bRecvData(1024) As Byte
    
    sCardBin = "222222"
    
    ret = CHK_CASHIC_CARDBIN(sCardBin, bRecvData(0))
    
    MsgBox (ret)
    MsgBox (StrConv(bRecvData, vbUnicode))
End Sub

Private Sub Command31_Click()
    FS = Chr$(&H1C)
    US = Chr$(&H1F)
    
    Dim send_data As String
    Dim recv_data As String
    
    
    Dim bReceData(8192) As Byte
    
        
    Dim halbu As String
        
    
    Text1.Text = ""
    Text2.Text = ""
    Text3.Text = ""
    Text4.Text = ""
    Text5.Text = ""
    Text6.Text = ""
    Text7.Text = ""
    Text8.Text = ""
    Text9.Text = ""
    Text10.Text = ""
    Text11.Text = ""
    Text12.Text = ""
    Text13.Text = ""
    Text14.Text = ""
    Text15.Text = ""
    Text16.Text = ""
    Text17.Text = ""
    
    Text_001.Text = ""
    Text_002.Text = ""
    Text_003.Text = ""
    Text_005.Text = ""
    Text_006.Text = ""
    Text_004.Text = ""
    Text_007.Text = ""
    Text_008.Text = ""
    Text_009.Text = ""
    Text_010.Text = ""
    Text_011.Text = ""
    Text_012.Text = ""
    Text_013.Text = ""
    Text_014.Text = ""
    Text_015.Text = ""
                    
    MPBugaYN.Text = ""
    MPBizcd.Text = ""
    MPBugainfo.Text = ""
    MPFiller2.Text = ""
                
    halbu = Format(ComboHalbu.ListIndex, "00")
    
    send_data = "020M" + US + "2" + US + "0200" + FS + "10" + FS + "C" + FS + TextMoney.Text + FS + TextTax.Text + FS + TextBongsa.Text + FS + halbu + FS + "" + FS + "" + FS + TCATID.Text + FS + FS + FS + FS + FS + FS + FS + FS + "" + FS + ApprPersonno.Text + FS + SignData.Text + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS + US + "0200" + FS + "10" + FS + "C" + FS + "10" + FS + FS + FS + "00" + FS + FS + FS + "2720084001" + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + US
    TextData.Text = send_data
    
    
    Dim m As Long
    m = NICEVCATMULTI(send_data, bReceData(0))
    
    
    If m <> 1 Then
        MsgBox (m)  '리턴값 처리 꼭 해주세요!!!!
        Exit Sub
    End If
    
    recv_data = StrConv(bReceData, vbUnicode)
    RecvData.Text = recv_data
    
End Sub

Private Sub Command4_Click()
    Dim ret As Long
    ret = READER_RESET(Text18.Text)
End Sub

Private Sub Command5_Click()
    
    Dim m As Long
    Dim bReceData(1024) As Byte
    m = GET_APPR(bReceData(0))
    MsgBox (m)  '리턴값 처리 꼭 해주세요!!!!
    
    If m <> 1 Then
        Exit Sub
    End If
    
    recv_data = StrConv(bReceData, vbUnicode)
    RecvData.Text = recv_data
End Sub

Private Sub Command6_Click()
    FS = Chr$(&H1C)
    
    Dim send_data As String
    Dim recv_data As String
    
    
    Dim bReceData(8192) As Byte
    
        
    Dim halbu As String
        
    
    Text1.Text = ""
    Text2.Text = ""
    Text3.Text = ""
    Text4.Text = ""
    Text5.Text = ""
    Text6.Text = ""
    Text7.Text = ""
    Text8.Text = ""
    Text9.Text = ""
    Text10.Text = ""
    Text11.Text = ""
    Text12.Text = ""
    Text13.Text = ""
    Text14.Text = ""
    Text15.Text = ""
    Text16.Text = ""
    Text17.Text = ""
    
    Text_001.Text = ""
    Text_002.Text = ""
    Text_003.Text = ""
    Text_005.Text = ""
    Text_006.Text = ""
    Text_004.Text = ""
    Text_007.Text = ""
    Text_008.Text = ""
    Text_009.Text = ""
    Text_010.Text = ""
    Text_011.Text = ""
    Text_012.Text = ""
    Text_013.Text = ""
    Text_014.Text = ""
    Text_015.Text = ""
                    
    MPBugaYN.Text = ""
    MPBizcd.Text = ""
    MPBugainfo.Text = ""
    MPFiller2.Text = ""
                
    halbu = Format(ComboHalbu.ListIndex, "00")
    
    Select Case (ComboDeal.ListIndex)
    Case 0
        send_data = "0200" + FS + "10" + FS + "C" + FS + TextMoney.Text + FS + TextTax.Text + FS + TextBongsa.Text + FS + halbu + FS + "" + FS + "" + FS + TCATID.Text + FS + FS + FS + FS + FS + FS + FS + FS + "" + FS + ApprPersonno.Text + FS + SignData.Text + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
        'send_data = "0200" + FS + "10" + FS + "C" + FS + TextMoney.Text + FS + TextTax.Text + FS + TextBongsa.Text + FS + halbu + FS + "" + FS + "" + FS + TCATID.Text + FS + FS + FS + FS + FS + FS + FS + FS + "" + FS + FS + SignData.Text + FS + "Y" + FS + "CHA" + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
    Case 1
        send_data = "0200" + FS + "10" + FS + "F" + FS + TextMoney.Text + FS + TextTax.Text + FS + TextBongsa.Text + FS + halbu + FS + "" + FS + "" + FS + TCATID.Text + FS + FS + FS + FS + FS + FS + FS + FS + "" + FS + FS + SignData.Text + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
    Case 2
        send_data = "0420" + FS + "10" + FS + "C" + FS + TextMoney.Text + FS + TextTax.Text + FS + TextBongsa.Text + FS + halbu + FS + TextAgreeNum.Text + FS + TextAgreeDate.Text + FS + TCATID.Text + FS + FS + FS + FS + FS + FS + FS + FS + "" + FS + ApprPersonno.Text + FS + SignData.Text + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
    Case 3
        halbu = Format(ComboHalbu.ListIndex + 1, "00")
                
        If Option1.Value = True Then
            send_data = "0200" + FS + "21" + FS + "K" + FS + TextMoney.Text + FS + TextTax.Text + FS + TextBongsa.Text + FS + halbu + FS + "" + FS + "" + FS + TCATID.Text + FS + FS + FS + FS + FS + FS + FS + FS + "" + FS + FS + SignData.Text + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
        ElseIf Option2.Value = True Then
            send_data = "0200" + FS + "21" + FS + "P" + FS + TextMoney.Text + FS + TextTax.Text + FS + TextBongsa.Text + FS + halbu + FS + "" + FS + "" + FS + TCATID.Text + FS + FS + FS + Textcashno.Text + FS + FS + FS + FS + FS + "" + FS + FS + SignData.Text + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
        ElseIf Option3.Value = True Then
            send_data = "0200" + FS + "21" + FS + "C" + FS + TextMoney.Text + FS + TextTax.Text + FS + TextBongsa.Text + FS + halbu + FS + "" + FS + "" + FS + TCATID.Text + FS + FS + FS + FS + FS + FS + FS + FS + "" + FS + FS + SignData.Text + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
        Else
            send_data = "0200" + FS + "21" + FS + "T" + FS + TextMoney.Text + FS + TextTax.Text + FS + TextBongsa.Text + FS + halbu + FS + "" + FS + "" + FS + TCATID.Text + FS + FS + FS + FS + FS + FS + FS + FS + "" + FS + FS + SignData.Text + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
        End If
    Case 4
        halbu = Format(ComboHalbu.ListIndex + 1, "00")
        
        If Option1.Value = True Then
            send_data = "0420" + FS + "21" + FS + "K" + FS + TextMoney.Text + FS + TextTax.Text + FS + TextBongsa.Text + FS + halbu + FS + TextAgreeNum.Text + FS + TextAgreeDate.Text + FS + TCATID.Text + FS + FS + FS + FS + FS + FS + FS + FS + "" + FS + FS + SignData.Text + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
        ElseIf Option2.Value = True Then
            send_data = "0420" + FS + "21" + FS + "P" + FS + TextMoney.Text + FS + TextTax.Text + FS + TextBongsa.Text + FS + halbu + FS + TextAgreeNum.Text + FS + TextAgreeDate.Text + FS + TCATID.Text + FS + FS + FS + Textcashno.Text + FS + FS + FS + FS + FS + "" + FS + FS + SignData.Text + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
        ElseIf Option3.Value = True Then
            send_data = "0420" + FS + "21" + FS + "C" + FS + TextMoney.Text + FS + TextTax.Text + FS + TextBongsa.Text + FS + halbu + FS + TextAgreeNum.Text + FS + TextAgreeDate.Text + FS + TCATID.Text + FS + FS + FS + FS + FS + FS + FS + FS + "" + FS + FS + SignData.Text + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
        Else
            send_data = "0420" + FS + "21" + FS + "T" + FS + TextMoney.Text + FS + TextTax.Text + FS + TextBongsa.Text + FS + halbu + FS + TextAgreeNum.Text + FS + TextAgreeDate.Text + FS + TCATID.Text + FS + FS + FS + FS + FS + FS + FS + FS + "" + FS + FS + SignData.Text + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
        End If

    Case 5
        send_data = "0200" + FS + "UP" + FS + "C" + FS + TextMoney.Text + FS + TextTax.Text + FS + TextBongsa.Text + FS + halbu + FS + "" + FS + "" + FS + TCATID.Text + FS + FS + FS + FS + FS + FS + FS + FS + "" + FS + FS + SignData.Text + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
    Case 6
        send_data = "0420" + FS + "UP" + FS + "C" + FS + TextMoney.Text + FS + TextTax.Text + FS + TextBongsa.Text + FS + halbu + FS + TextAgreeNum.Text + FS + TextAgreeDate.Text + FS + TCATID.Text + FS + FS + FS + FS + FS + FS + FS + FS + "" + FS + FS + SignData.Text + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
    Case 7
        Dim Billtpcd As String
        Dim Billmoneycd As String
        
        Billtpcd = Left(Billtp.Text, 2)
        Billmoneycd = Left(Billmoney.Text, 2)
        
        send_data = "0200" + FS + "20" + FS + "K" + FS + Billtpcd + FS + Billmoneycd + FS + Billno.Text + FS + Billdt.Text + FS + billsn.Text + FS + billamt.Text + FS + Billserial.Text + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
    Case 8
        send_data = "0200" + FS + "I1" + FS + "00" + FS + TextBongsa.Text + FS + TextTax.Text + FS + TextMoney.Text + FS + FS + FS + TCATID.Text + FS + FS + FS + FS + "" + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
        'send_data = "0200" + FS + "I1" + FS + "03" + FS + TextBongsa.Text + FS + TextTax.Text + FS + TextMoney.Text + FS + FS + FS + TCATID.Text + FS + FS + FS + FS + "" + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
    Case 9
        send_data = "0420" + FS + "I4" + FS + "00" + FS + TextBongsa.Text + FS + TextTax.Text + FS + TextMoney.Text + FS + TextAgreeNum.Text + FS + TextAgreeDate.Text + FS + TCATID.Text + FS + FS + FS + FS + "" + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
        'send_data = "0420" + FS + "I4" + FS + "03" + FS + TextBongsa.Text + FS + TextTax.Text + FS + TextMoney.Text + FS + TextAgreeNum.Text + FS + TextAgreeDate.Text + FS + TCATID.Text + FS + FS + FS + FS + "" + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
    Case 10
        'send_data = "0200" + FS + "I3" + FS + "00" + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + "" + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
        send_data = "0200" + FS + "I3" + FS + "03" + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + "" + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
    Case 11
        send_data = "0200" + FS + "I2" + FS + "00" + FS + TextBongsa.Text + FS + TextTax.Text + FS + TextMoney.Text + FS + TextAgreeNum.Text + FS + TextAgreeDate.Text + FS + TCATID.Text + FS + FS + FS + FS + "" + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
        'send_data = "0200" + FS + "I2" + FS + "03" + FS + TextBongsa.Text + FS + TextTax.Text + FS + TextMoney.Text + FS + TextAgreeNum.Text + FS + TextAgreeDate.Text + FS + TCATID.Text + FS + FS + FS + FS + "" + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
    Case 12
        send_data = "0420" + FS + "I2" + FS + "00" + FS + TextBongsa.Text + FS + TextTax.Text + FS + TextMoney.Text + FS + TextAgreeNum.Text + FS + TextAgreeDate.Text + FS + TCATID.Text + FS + FS + FS + FS + "" + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
        'send_data = "0420" + FS + "I2" + FS + "03" + FS + TextBongsa.Text + FS + TextTax.Text + FS + TextMoney.Text + FS + TextAgreeNum.Text + FS + TextAgreeDate.Text + FS + TCATID.Text + FS + FS + FS + FS + "" + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
    Case 13
        send_data = "0420" + FS + "10" + FS + "Y" + FS + TextMoney.Text + FS + TextTax.Text + FS + TextBongsa.Text + FS + halbu + FS + TextAgreeNum.Text + FS + TextAgreeDate.Text + FS + TCATID.Text + FS + FS + FS + Textcashno.Text + FS + FS + FS + FS + FS + "" + FS + FS + SignData.Text + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
    Case 14
        send_data = "0420" + FS + "10" + FS + "N" + FS + TextMoney.Text + FS + TextTax.Text + FS + TextBongsa.Text + FS + halbu + FS + TextAgreeNum.Text + FS + TextAgreeDate.Text + FS + TCATID.Text + FS + FS + FS + Textcashno.Text + FS + FS + FS + FS + FS + "" + FS + FS + SignData.Text + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
    Case 15
        halbu = Format(ComboHalbu.ListIndex + 1, "00")
        send_data = "0420" + FS + "21" + FS + "N" + FS + TextMoney.Text + FS + TextTax.Text + FS + TextBongsa.Text + FS + halbu + FS + TextAgreeNum.Text + FS + TextAgreeDate.Text + FS + TCATID.Text + FS + FS + FS + FS + FS + FS + FS + FS + "" + FS + FS + SignData.Text + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
    Case 16 '현금IC무카드취소
        send_data = "0420" + FS + "I4" + FS + "02" + FS + TextBongsa.Text + FS + TextTax.Text + FS + TextMoney.Text + FS + TextAgreeNum.Text + FS + TextAgreeDate.Text + FS + TCATID.Text + FS + FS + FS + FS + "" + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
    Case 17 'DCC 결제
        send_data = "0200" + FS + "DC" + FS + "C" + FS + TextMoney.Text + FS + TextTax.Text + FS + TextBongsa.Text + FS + halbu + FS + FS + FS + TCATID.Text + FS + "410" + FS + TextMoney.Text + FS + "0" + FS + FS + FS + FS + FS + FS + "" + FS + SignData.Text + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
    Case 19 '포인트승인
        send_data = "0300" + FS + Dealgb.Text + FS + "I" + FS + TextMoney.Text + FS + TextTax.Text + FS + TextBongsa.Text + FS + halbu + FS + "" + FS + "" + FS + FS + FS + FS + FS + "" + FS + FS + FS + FS + FS + FS + "" + FS + "" + FS + "" + FS + "" + FS + "" + FS + SignData.Text + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
    Case 20 '포인트취소
        Dealgb.Text = "70"
        send_data = "0520" + FS + Dealgb.Text + FS + "I" + FS + TextMoney.Text + FS + TextTax.Text + FS + TextBongsa.Text + FS + halbu + FS + TextAgreeNum.Text + FS + TextAgreeDate.Text + FS + FS + FS + FS + FS + "" + FS + FS + FS + FS + FS + FS + "" + FS + "" + FS + Text_UniNum.Text + FS + "" + FS + "" + FS + SignData.Text + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
    Case 21 '멤버쉽승인
        '캐시백조회
        'send_data = "0320" + FS + "40" + FS + "I" + FS + "1" + FS + "00" + FS + "03" + FS + "" + FS + "" + FS + "" + FS + TCATID.Text + FS + FS + FS + FS + FS + FS + FS + FS + "" + FS + FS + "" + FS + "HPS" + FS + "H1" + FS + FS + FS
        '캐시백사용
        Dealgb.Text = "40"
        send_data = "0320" + FS + Dealgb.Text + FS + "I" + FS + TextMoney.Text + FS + TextTax.Text + FS + TextBongsa.Text + FS + Textcashno.Text + FS + "" + FS + "" + FS + FS + FS + FS + FS + FS + FS + FS + FS + "" + FS + FS + "" + FS + "" + FS + "" + FS + FS + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
    Case 22 '멤버쉽취소
        '캐시백사용취소
        Dealgb.Text = "40"
        send_data = "0540" + FS + Dealgb.Text + FS + "I" + FS + TextMoney.Text + FS + TextTax.Text + FS + TextBongsa.Text + FS + Textcashno.Text + FS + TextAgreeNum.Text + FS + TextAgreeDate.Text + FS + FS + FS + FS + FS + FS + FS + FS + FS + "" + FS + FS + "" + FS + "" + FS + "" + FS + FS + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
    Case 23 '서명패드MST승인
        send_data = "0200" + FS + "10" + FS + "M" + FS + TextMoney.Text + FS + TextTax.Text + FS + TextBongsa.Text + FS + halbu + FS + "" + FS + "" + FS + TCATID.Text + FS + FS + FS + FS + FS + FS + FS + FS + "" + FS + FS + SignData.Text + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
    Case 24 '서명패드MST취소
        send_data = "0420" + FS + "10" + FS + "M" + FS + TextMoney.Text + FS + TextTax.Text + FS + TextBongsa.Text + FS + halbu + FS + TextAgreeNum.Text + FS + TextAgreeDate.Text + FS + TCATID.Text + FS + FS + FS + FS + FS + FS + FS + FS + "" + FS + FS + SignData.Text + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
    Case 25 'LGT할인승인
        send_data = "0300" + FS + "90" + FS + "I" + FS + "100" + FS + FS + FS + "00" + FS + "" + FS + "" + FS + FS + FS + FS + FS + FS + FS + FS + FS + "" + FS + FS + FS + FS + FS + FS + FS + SignData.Text + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
    Case 26 'LGT할인취소
        send_data = "0520" + FS + "90" + FS + "I" + FS + "100" + FS + FS + FS + "00" + FS + TextAgreeNum.Text + FS + TextAgreeDate.Text + FS + FS + FS + FS + FS + FS + FS + FS + FS + "" + FS + FS + FS + FS + FS + FS + FS + SignData.Text + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
    Case 27 'SKP토큰
        send_data = "0300" + FS + Dealgb.Text + FS + "L" + FS + TextMoney.Text + FS + TextTax.Text + FS + TextBongsa.Text + FS + halbu + FS + "" + FS + "" + FS + FS + FS + FS + Textcashno.Text + FS + "" + FS + FS + FS + FS + "Filler" + FS + "19881130107" + FS + "" + FS + "" + FS + "" + FS + "USERID12345678901234이주용" + FS + "   01023720000SKT" + FS + SignData.Text + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
    Case 28 'SKP토큰취소
        '토큰
        send_data = "0520" + FS + Dealgb.Text + FS + "L" + FS + TextMoney.Text + FS + TextTax.Text + FS + TextBongsa.Text + FS + halbu + FS + TextAgreeNum.Text + FS + TextAgreeDate.Text + FS + FS + FS + FS + Textcashno.Text + FS + "" + FS + FS + FS + FS + "Filler" + FS + "19881130199" + FS + "" + FS + "" + FS + "" + FS + "USERID12345678901234이주용" + FS + "   01023720000SKT" + FS + SignData.Text + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
    Case 29 '카드정보조회
        send_data = "0300" + FS + "10" + FS + "I" + FS + "1" + FS + "0" + FS + "0" + FS + "00" + FS + "" + FS + "" + FS + FS + FS + FS + FS + "" + FS + FS + FS + FS + FS + FS + "CNS" + FS + "" + FS + "" + FS + "" + FS + "" + FS + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
    
    Case 30 'NICE HIPASS(등록:N1)
        send_data = "0300" + FS + "N1" + FS + "L" + FS + TextMoney.Text + FS + TextTax.Text + FS + TextBongsa.Text + FS + halbu + FS + "" + FS + "" + FS + FS + FS + FS + FS + FS + FS + FS + FS + "Filler" + FS + "881130   00" + FS + FS + FS + FS + FS + "BSM2013055|이주용1" + FS + "" + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
    Case 31 'NICE HIPASS(승인:N2)
        send_data = "0300" + FS + "N2" + FS + "L" + FS + TextMoney.Text + FS + TextTax.Text + FS + TextBongsa.Text + FS + halbu + FS + "" + FS + "" + FS + FS + FS + FS + Textcashno.Text + FS + FS + FS + FS + FS + "Filler" + FS + "" + FS + FS + FS + FS + FS + "BSM2013055|이주용1" + FS + SignData.Text + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
    Case 32 'NICE HIPASS(취소:N2)
        send_data = "0520" + FS + "N2" + FS + "L" + FS + TextMoney.Text + FS + TextTax.Text + FS + TextBongsa.Text + FS + halbu + FS + TextAgreeNum.Text + FS + TextAgreeDate.Text + FS + FS + FS + FS + Textcashno.Text + FS + FS + FS + FS + FS + "Filler" + FS + "" + FS + FS + FS + FS + FS + "BSM2013055|이주용1" + FS + SignData.Text + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
    Case 33 'NICE HIPASS(삭제:N3)
        send_data = "0300" + FS + "N3" + FS + "L" + FS + TextMoney.Text + FS + TextTax.Text + FS + TextBongsa.Text + FS + halbu + FS + "" + FS + "" + FS + FS + FS + FS + Textcashno.Text + FS + FS + FS + FS + FS + "Filler" + FS + "" + FS + FS + FS + FS + FS + "BSM2013055|이주용1" + FS + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
        
    Case 34 '그린카드적립승인
        send_data = "0320" + FS + "48" + FS + "I" + FS + TextMoney.Text + FS + TextTax.Text + FS + TextBongsa.Text + FS + FS + "" + FS + "" + FS + TCATID.Text + FS + FS + FS + FS + FS + FS + FS + FS + "" + FS + FS + "HPS" + FS + "" + FS + Textcashno.Text + FS + FS + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
    Case 35 '그린카드적립취소
        send_data = "0540" + FS + "48" + FS + "I" + FS + TextMoney.Text + FS + TextTax.Text + FS + TextBongsa.Text + FS + FS + TextAgreeNum.Text + FS + TextAgreeDate.Text + FS + TCATID.Text + FS + FS + FS + FS + FS + FS + FS + "" + FS + "" + FS + FS + "HPS" + FS + "" + FS + Textcashno.Text + FS + FS + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
    
    Case 36 'DCC환율조회(POS 2TR)
        send_data = "0200" + FS + "D1" + FS + "C" + FS + TextMoney.Text + FS + TextTax.Text + FS + TextBongsa.Text + FS + halbu + FS + FS + FS + TCATID.Text + FS + "410" + FS + TextMoney.Text + FS + "0" + FS + FS + Textcashno.Text + FS + FS + FS + FS + "" + FS + SignData.Text + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
    Case 37 'DCC원화통화승인(POS 2TR)
        send_data = "0200" + FS + "D2" + FS + "C" + FS + TextMoney.Text + FS + TextTax.Text + FS + TextBongsa.Text + FS + halbu + FS + FS + FS + TCATID.Text + FS + "410" + FS + TextMoney.Text + FS + "0" + FS + FS + Textcashno.Text + FS + FS + FS + FS + "" + FS + SignData.Text + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
    Case 38 'DCC자국통화승인(POS 2TR)
        send_data = "0200" + FS + "D3" + FS + "C" + FS + TextMoney.Text + FS + TextTax.Text + FS + TextBongsa.Text + FS + halbu + FS + FS + FS + TCATID.Text + FS + "410" + FS + TextMoney.Text + FS + "0" + FS + FS + Textcashno.Text + FS + FS + FS + FS + "" + FS + SignData.Text + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
    
    Case 39 '신용부분취소
        send_data = "0520" + FS + "30" + FS + "I" + FS + TextMoney.Text + FS + TextTax.Text + FS + TextBongsa.Text + FS + halbu + FS + TextAgreeNum.Text + FS + TextAgreeDate.Text + FS + FS + FS + FS + FS + "" + FS + FS + FS + FS + FS + "P000000001004" + FS + "PCL" + FS + "" + FS + "" + FS + "" + FS + FS + SignData.Text + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
    Case 40 'NICE HIPASS(일련번호취소:N2)
        send_data = "0520" + FS + "N2" + FS + "N" + FS + TextMoney.Text + FS + TextTax.Text + FS + TextBongsa.Text + FS + halbu + FS + TextAgreeNum.Text + FS + TextAgreeDate.Text + FS + FS + FS + FS + Textcashno.Text + FS + FS + FS + FS + FS + "Filler" + FS + "" + FS + FS + FS + FS + FS + "BSM2013055|이주용1" + FS + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
    Case 41 '무카드신용부분취소(LJY20220224)
        send_data = "0520" + FS + "30" + FS + "N" + FS + TextMoney.Text + FS + TextTax.Text + FS + TextBongsa.Text + FS + halbu + FS + TextAgreeNum.Text + FS + TextAgreeDate.Text + FS + TCATID.Text + FS + FS + FS + Textcashno.Text + FS + FS + FS + FS + FS + "" + FS + "P000000001004" + FS + "PCL" + FS + FS + FS + FS + FS + FS + MPBugaYN.Text + FS + MPBugainfo.Text + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
    Case 42 '(행안부)모바일운전면허증
        send_data = "0200" + FS + "HM" + FS + Text_Num.Text + FS + Text_QR.Text + FS + Text_Filler1.Text + FS + Text_Filler2.Text + FS
    Case 43 '컵보증금
        send_data = "0200" + FS + "10" + FS + "C" + FS + TextMoney.Text + FS + TextTax.Text + FS + TextBongsa.Text + FS + halbu + FS + "" + FS + "" + FS + TCATID.Text + FS + FS + FS + FS + FS + FS + FS + FS + "" + FS + FS + SignData.Text + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS + Text_MsgText.Text + FS + Text_Kind.Text + FS + Text_UniNum.Text + FS + Text_Domain.Text + FS + Text_IP + FS
    Case 44 'SKP 토큰승인
        send_data = "0300" + FS + "S2" + FS + "L" + FS + TextMoney.Text + FS + TextTax.Text + FS + TextBongsa.Text + FS + halbu + FS + "" + FS + "" + FS + TCATID.Text + FS + FS + FS + Textcashno.Text + FS + FS + FS + FS + FS + "" + FS + FS + SignData.Text + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS + Text_MsgText.Text + FS + Text_Kind.Text + FS + Text_UniNum.Text + FS + Text_Domain.Text + FS + Text_IP + FS
    Case 45 'NICE HIPASS(등록:N1)
        send_data = "0300" + FS + "N1" + FS + "s" + FS + TextMoney.Text + FS + TextTax.Text + FS + TextBongsa.Text + FS + halbu + FS + "" + FS + "" + FS + FS + FS + FS + FS + FS + FS + FS + FS + "Filler" + FS + "" + FS + FS + FS + FS + FS + "BSM" + Format(Now, "YYYYMMDDhhmmsszzz") + FS + "" + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
    Case 46 'NICE HIPASS(등록+인증X:N6)
        send_data = "0300" + FS + "N6" + FS + "L" + FS + TextMoney.Text + FS + TextTax.Text + FS + TextBongsa.Text + FS + halbu + FS + "" + FS + "" + FS + FS + FS + FS + FS + FS + FS + FS + FS + "Filler" + FS + "" + FS + FS + FS + FS + FS + "CHA" + Format(Now, "YYYYMMDDhhmmsszzz") + FS + "" + FS + "Y" + FS + "CHA" + FS + "O15050928" + FS + MPFiller2.Text + FS + FS
    Case 47 '무서명 신용승인
        send_data = "0200" + FS + "10" + FS + "n" + FS + TextMoney.Text + FS + TextTax.Text + FS + TextBongsa.Text + FS + halbu + FS + "" + FS + "" + FS + TCATID.Text + FS + FS + FS + FS + FS + FS + FS + FS + "" + FS + FS + SignData.Text + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
    Case 48 '카드빈 화이트리스트 체크
        send_data = "0200" + FS + "10" + FS + "C" + FS + TextMoney.Text + FS + TextTax.Text + FS + TextBongsa.Text + FS + halbu + FS + "" + FS + "" + FS + TCATID.Text + FS + FS + FS + FS + FS + "CWB" + FS + FS + FS + "" + FS + ApprPersonno.Text + FS + SignData.Text + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
    Case 49 '카드빈 블랙리스트 체크
        send_data = "0200" + FS + "10" + FS + "C" + FS + TextMoney.Text + FS + TextTax.Text + FS + TextBongsa.Text + FS + halbu + FS + "" + FS + "" + FS + TCATID.Text + FS + FS + FS + FS + FS + "CBB" + FS + FS + FS + "" + FS + ApprPersonno.Text + FS + SignData.Text + FS + MPBugaYN.Text + FS + MPBizcd.Text + FS + MPBugainfo.Text + FS + MPFiller2.Text + FS
         
   End Select
    TextData.Text = send_data
    
    
    Dim m As Long
    m = NICEVCAT(send_data, bReceData(0))
    
    
    If m <> 1 Then
        MsgBox (m)  '리턴값 처리 꼭 해주세요!!!!
        Exit Sub
    End If
    
    recv_data = StrConv(bReceData, vbUnicode)
    RecvData.Text = recv_data
    TextRecv.Text = recv_data

'Exit Sub

    If ComboDeal.ListIndex = 7 Then
        Exit Sub
    End If
    
    '=============================================================================================================
    
    Dim i, j, k As Long
    i = 0
    j = 0
    k = 1
    
    If ComboDeal.ListIndex = 8 Or ComboDeal.ListIndex = 9 Or ComboDeal.ListIndex = 10 Or ComboDeal.ListIndex = 11 Or ComboDeal.ListIndex = 12 Then
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
                    Text6.Text = Mid(recv_data, k, i - k)
                Case 5
                    Text5.Text = Mid(recv_data, k, i - k)
                Case 6
                    Text4.Text = Mid(recv_data, k, i - k)
                Case 7
                    Text14.Text = Mid(recv_data, k, i - k)
                Case 8
                    Text9.Text = Mid(recv_data, k, i - k)
                Case 9
                    Text8.Text = Mid(recv_data, k, i - k)
                    TextAgreeNum.Text = Text8.Text
                Case 10
                    Text_001.Text = Mid(recv_data, k, i - k)
                Case 11
                    Text_002.Text = Mid(recv_data, k, i - k)
                Case 12
                    Text_003.Text = Mid(recv_data, k, i - k)
                Case 13
                    Text_005.Text = Mid(recv_data, k, i - k)
                Case 14
                    Text_006.Text = Mid(recv_data, k, i - k)
                Case 15
                    Text_004.Text = Mid(recv_data, k, i - k)
                Case 16
                    Text_007.Text = Mid(recv_data, k, i - k)
                Case 17
                    Text_008.Text = Mid(recv_data, k, i - k)
                Case 18
                    Text_009.Text = Mid(recv_data, k, i - k)
                Case 19
                    Text_010.Text = Mid(recv_data, k, i - k)
                Case 20
                    Text_011.Text = Mid(recv_data, k, i - k)
                Case 21
                    Text_012.Text = Mid(recv_data, k, i - k)
                Case 22
                    Text_013.Text = Mid(recv_data, k, i - k)
                Case 23
                    Text_014.Text = Mid(recv_data, k, i - k)
                Case 24
                    Text_015.Text = Mid(recv_data, k, i - k)
                End Select
                
                k = i + 1
                
                If j = 24 Then '종료
                    Exit Do
                End If
            End If
        Loop
    ElseIf ComboDeal.ListIndex = 30 Or ComboDeal.ListIndex = 31 Or ComboDeal.ListIndex = 32 Or ComboDeal.ListIndex = 33 Then
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
                    TextAgreeNum.Text = Text8.Text
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
                    Text19.Text = Mid(recv_data, k, i - k)
                Case 19
                    Text20.Text = Mid(recv_data, k, i - k)
                Case 20
                    Text21.Text = Mid(recv_data, k, i - k)
                Case 21
                    Text22.Text = Mid(recv_data, k, i - k)
                Case 27
                    Text23.Text = Mid(recv_data, k, i - k)
                End Select
                
                k = i + 1
                
                If j = 27 Then '종료
                    Exit Do
                End If
            End If
        Loop
    ElseIf ComboDeal.ListIndex = 42 Then
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
                    RecvQR.Text = Mid(recv_data, k, i - k)
                Case 5
                    RecvTrx.Text = Mid(recv_data, k, i - k)
                Case 6
                    RecvCode.Text = Mid(recv_data, k, i - k)
                Case 7
                    RecvMsg.Text = Mid(recv_data, k, i - k)
                Case 8
                    RecvFiller1.Text = Mid(recv_data, k, i - k)
                Case 9
                    RecvFiller2.Text = Mid(recv_data, k, i - k)
                End Select
                
                k = i + 1
                
                If j = 9 Then '종료
                    Exit Do
                End If
            End If
        Loop
    Else
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
                    TextAgreeNum.Text = Text8.Text
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
                    Text19.Text = Mid(recv_data, k, i - k)
                Case 19
                    Text20.Text = Mid(recv_data, k, i - k)
                Case 20
                    Text21.Text = Mid(recv_data, k, i - k)
                Case 21
                    Text22.Text = Mid(recv_data, k, i - k)
                End Select
                
                k = i + 1
                
                If j = 21 Then '종료
                    Exit Do
                End If
            End If
        Loop
    
    End If

End Sub

Private Sub Command7_Click()
    Dim ret As Long
    Dim bReceData(1024) As Byte
    ret = CHK_CARDBIN(bReceData(0))
    
    If ret > 0 Then
       MsgBox (StrConv(bReceData, vbUnicode))
    Else
       MsgBox ("실패")
    End If
       
        
    
End Sub

Private Sub Command8_Click()
    
    Dim ret As Long
    ret = CHK_CASHIC()
    'ret = CHK_CASHIC_MP()
    MsgBox (ret)

End Sub

Private Sub Command9_Click()
    Dim ret As Long
    ret = READER_RESET("0") '배출요청은 무조건 인자에 0
End Sub

Private Sub Form_Initialize()
    Command11.Caption = "CHK_MEMBERSHIP" + vbLf + "(멤버쉽카드번호조회)"
    Command13.Caption = "CHK_CASHIC_MP" + vbLf + "(멀티패드 현금IC카드여부확인)"
    Command14.Caption = "CHK_CARDIN_MP" + vbLf + "(멀티패드 IC 카드 확인)"
End Sub
Private Sub Form_Load()
    ComboDeal.AddItem ("신용승인") '0
    ComboDeal.AddItem ("FALLBACK") '1
    ComboDeal.AddItem ("신용취소") '2
    ComboDeal.AddItem ("현금승인") '3
    ComboDeal.AddItem ("현금취소") '4
    ComboDeal.AddItem ("은련승인") '5
    ComboDeal.AddItem ("은련취소") '6
    ComboDeal.AddItem ("수표조회") '7
    ComboDeal.AddItem ("현금IC승인") '8
    ComboDeal.AddItem ("현금IC취소") '9
    ComboDeal.AddItem ("현금IC잔액조회") '10
    ComboDeal.AddItem ("현금IC승인결과") '11
    ComboDeal.AddItem ("현금IC취소결과") '12
    ComboDeal.AddItem ("신용(서명O)일련번호취소") '13
    ComboDeal.AddItem ("신용(서명X)일련번호취소") '14
    ComboDeal.AddItem ("현금무카드취소") '15
    ComboDeal.AddItem ("현금IC무카드취소") '16
    ComboDeal.AddItem ("DCC거래") '17
    ComboDeal.AddItem ("직전거래가져오기") '18
    ComboDeal.AddItem ("포인트승인") '19
    ComboDeal.AddItem ("포인트취소") '20
    ComboDeal.AddItem ("멤버쉽승인") '21
    ComboDeal.AddItem ("멤버쉽취소") '22
    ComboDeal.AddItem ("서명패드MST승인") '23
    ComboDeal.AddItem ("서명패드MST취소") '24
    ComboDeal.AddItem ("LGT할인승인") '25
    ComboDeal.AddItem ("LGT할인취소") '26
    ComboDeal.AddItem ("SKP토큰(거래유형S1)") '27
    ComboDeal.AddItem ("SKP토큰취소(거래유형S2)") '28
    ComboDeal.AddItem ("카드정보조회") '29
    ComboDeal.AddItem ("NICE HIPASS(등록:N1)") '30
    ComboDeal.AddItem ("NICE HIPASS(승인:N2)") '31
    ComboDeal.AddItem ("NICE HIPASS(취소:N2)") '32
    ComboDeal.AddItem ("NICE HIPASS(삭제:N3)") '33
    ComboDeal.AddItem ("그린카드적립승인") '34
    ComboDeal.AddItem ("그린카드적립취소") '35
    ComboDeal.AddItem ("DCC환율조회(POS 2TR)") '36
    ComboDeal.AddItem ("DCC원화통화승인(POS 2TR)") '37
    ComboDeal.AddItem ("DCC자국통화승인(POS 2TR)") '38
    ComboDeal.AddItem ("신용부분취소") '39
    ComboDeal.AddItem ("NICE HIPASS(일련번호취소:N2)") '40
    ComboDeal.AddItem ("무카드신용부분취소") '41
    ComboDeal.AddItem ("(행안부)모바일운전면허증") '42
    ComboDeal.AddItem ("컵보증금") '43
    ComboDeal.AddItem ("SKT토큰승인") '44
    ComboDeal.AddItem ("NICE HIPASS(등록:N1,s)") '45
    ComboDeal.AddItem ("NICE HIPASS(등록,인증X:N6)") '46
    ComboDeal.AddItem ("무서명신용승인")  '4７
    ComboDeal.AddItem ("카드빈 화이트리스트 승인")  '48
    ComboDeal.AddItem ("카드빈 블랙리스트 승인")  '49
    ComboDeal.ListIndex = 0
    
    ComboHalbu.Clear
    ComboHalbu.AddItem ("0개월")
    ComboHalbu.AddItem ("1개월")
    ComboHalbu.AddItem ("2개월")
    ComboHalbu.AddItem ("3개월")
    ComboHalbu.AddItem ("4개월")
    ComboHalbu.AddItem ("5개월")
    ComboHalbu.AddItem ("6개월")
    ComboHalbu.AddItem ("7개월")
    ComboHalbu.AddItem ("8개월")
    ComboHalbu.AddItem ("9개월")
    ComboHalbu.AddItem ("10개월")
    ComboHalbu.AddItem ("11개월")
    ComboHalbu.AddItem ("12개월")
    ComboHalbu.ListIndex = 0
    
    Billtp.AddItem ("00 자기앞수표")
    Billtp.AddItem ("01 가계수표")
    Billtp.AddItem ("02 당좌수표")
    Billtp.ListIndex = 0
    
    Billmoney.AddItem ("13 10만원")
    Billmoney.AddItem ("14 30만원")
    Billmoney.AddItem ("15 50만원")
    Billmoney.AddItem ("16 100만원")
    Billmoney.AddItem ("19 비정액")
    Billmoney.ListIndex = 0
    
    TextAgreeDate.Text = Format(Now, "YYMMDD")
    
    Dim ret As Long
    Dim iparr(100) As Byte
    Dim portarr(100) As Byte
    ret = Get_SvrInfo(iparr(0), portarr(0))
    Iptext.Text = StrConv(iparr, vbUnicode)
    porttext.Text = StrConv(portarr, vbUnicode)
    
    
    'MPBugainfo.Text = "환자명:홍길동|환자번호:18102900001|진료과모:내과(0001)|수납부서 : 입퇴원(0001)|수납원:아무개|       "
End Sub

Private Sub Form_keyDown(keycode As Integer, Shift As Integer)
    MsgBox (keycode)
End Sub

