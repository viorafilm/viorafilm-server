object Form1: TForm1
  Left = 232
  Top = 135
  Width = 728
  Height = 681
  Caption = #47308
  Color = clBtnFace
  Font.Charset = DEFAULT_CHARSET
  Font.Color = clWindowText
  Font.Height = -11
  Font.Name = 'MS Sans Serif'
  Font.Style = []
  OldCreateOrder = False
  OnCreate = FormCreate
  PixelsPerInch = 96
  TextHeight = 13
  object Label41: TLabel
    Left = 352
    Top = 152
    Width = 57
    Height = 13
    AutoSize = False
    Caption = #49688#54364#44552#50529
  end
  object Label42: TLabel
    Left = 24
    Top = 604
    Width = 135
    Height = 13
    Caption = #44032#47609#51216#45796#50868#47196#46300' '#53580#49828#53944#50668#48512
  end
  object Label43: TLabel
    Left = 200
    Top = 604
    Width = 111
    Height = 13
    Caption = #48512#51221#52712#49548' '#48120#49324#50857#49884' "Y"'
  end
  object GroupBox1: TGroupBox
    Left = 24
    Top = 32
    Width = 673
    Height = 185
    Caption = #49849#51064' '#50836#52397' DATA'
    TabOrder = 0
    object Label1: TLabel
      Left = 16
      Top = 24
      Width = 57
      Height = 13
      AutoSize = False
      Caption = #44144#47000#51333#47448
    end
    object Label2: TLabel
      Left = 16
      Top = 48
      Width = 22
      Height = 13
      Caption = #54624#48512
    end
    object Label3: TLabel
      Left = 192
      Top = 24
      Width = 57
      Height = 13
      AutoSize = False
      Caption = #44144#47000#44552#50529
    end
    object Label4: TLabel
      Left = 192
      Top = 48
      Width = 57
      Height = 13
      AutoSize = False
      Caption = #49849#51064#48264#54840
    end
    object Label5: TLabel
      Left = 344
      Top = 24
      Width = 83
      Height = 13
      Caption = #48512#44032#49464'('#51201#47549#44396#48516')'
    end
    object Label6: TLabel
      Left = 352
      Top = 48
      Width = 57
      Height = 13
      AutoSize = False
      Caption = #49849#51064#45216#51676
    end
    object Label7: TLabel
      Left = 504
      Top = 24
      Width = 94
      Height = 13
      Caption = #48393#49324#47308'('#54252#51064#53944#44396#48516')'
    end
    object Label8: TLabel
      Left = 536
      Top = 48
      Width = 32
      Height = 13
      Caption = 'CATID'
    end
    object Label31: TLabel
      Left = 16
      Top = 104
      Width = 73
      Height = 17
      AutoSize = False
      Caption = #49688#54364#51312#54924
      Font.Charset = DEFAULT_CHARSET
      Font.Color = clWindowText
      Font.Height = -13
      Font.Name = 'MS Sans Serif'
      Font.Style = [fsBold, fsUnderline]
      ParentFont = False
    end
    object Label32: TLabel
      Left = 16
      Top = 128
      Width = 57
      Height = 13
      AutoSize = False
      Caption = #49688#54364#51333#47448
    end
    object Label33: TLabel
      Left = 192
      Top = 128
      Width = 57
      Height = 13
      AutoSize = False
      Caption = #49688#54364#44428#51333
    end
    object Label34: TLabel
      Left = 352
      Top = 128
      Width = 57
      Height = 13
      AutoSize = False
      Caption = #49688#54364#48264#54840
    end
    object Label35: TLabel
      Left = 16
      Top = 152
      Width = 57
      Height = 13
      AutoSize = False
      Caption = #48156#54665#51068
    end
    object Label36: TLabel
      Left = 192
      Top = 152
      Width = 57
      Height = 13
      AutoSize = False
      Caption = #51452#48124#48264#54840
    end
    object Label37: TLabel
      Left = 352
      Top = 152
      Width = 57
      Height = 13
      AutoSize = False
      Caption = #49688#54364#44552#50529
    end
    object Label38: TLabel
      Left = 504
      Top = 152
      Width = 81
      Height = 13
      AutoSize = False
      Caption = #44228#51340#51068#47144#48264#54840
    end
    object Label39: TLabel
      Left = 192
      Top = 72
      Width = 249
      Height = 13
      Caption = #54788#44552#49885#48324#48264#54840'('#53664#53360'/Filler2/DCC POS 2TR '#54872#50984#51221#48372')'
    end
    object Label40: TLabel
      Left = 192
      Top = 96
      Width = 55
      Height = 13
      Caption = #49436#47749#45936#51060#53552
    end
    object ComboDeal: TComboBox
      Left = 72
      Top = 24
      Width = 113
      Height = 21
      ImeName = 'Microsoft IME 2010'
      ItemHeight = 13
      TabOrder = 0
      Text = 'ComboDeal'
      OnSelect = ComboDealSelect
    end
    object ComboHalbu: TComboBox
      Left = 72
      Top = 48
      Width = 113
      Height = 21
      ImeName = 'Microsoft IME 2010'
      ItemHeight = 13
      TabOrder = 1
      Text = 'ComboDeal'
    end
    object EditMoney: TEdit
      Left = 256
      Top = 24
      Width = 81
      Height = 21
      ImeName = 'Microsoft IME 2010'
      TabOrder = 2
      Text = '1004'
    end
    object EditAgreedate: TEdit
      Left = 416
      Top = 48
      Width = 81
      Height = 21
      ImeName = 'Microsoft IME 2010'
      TabOrder = 3
      Text = 'YYMMDD'
    end
    object EditTax: TEdit
      Left = 432
      Top = 24
      Width = 65
      Height = 21
      ImeName = 'Microsoft IME 2010'
      TabOrder = 4
      Text = '0'
    end
    object EditBongsa: TEdit
      Left = 600
      Top = 24
      Width = 57
      Height = 21
      ImeName = 'Microsoft IME 2010'
      TabOrder = 5
      Text = '0'
    end
    object CheckKeyin: TCheckBox
      Left = 16
      Top = 72
      Width = 161
      Height = 21
      Caption = #54788#44552#50689#49688#51613' Keyin '#44144#47000
      TabOrder = 6
    end
    object EditCatid: TEdit
      Left = 576
      Top = 48
      Width = 81
      Height = 21
      ImeName = 'Microsoft IME 2010'
      TabOrder = 7
    end
    object ButtonReq: TButton
      Left = 352
      Top = 96
      Width = 145
      Height = 21
      Caption = #49849#51064#50836#52397
      TabOrder = 8
      OnClick = ButtonReqClick
    end
    object ButtonCnl: TButton
      Left = 512
      Top = 96
      Width = 145
      Height = 21
      Caption = #52712#49548
      TabOrder = 9
      OnClick = ButtonCnlClick
    end
    object ComboBilltp: TComboBox
      Left = 80
      Top = 124
      Width = 97
      Height = 21
      ImeName = 'Microsoft IME 2010'
      ItemHeight = 13
      TabOrder = 10
      Text = 'ComboBilltp'
      OnSelect = ComboDealSelect
    end
    object ComboBillMoney: TComboBox
      Left = 256
      Top = 124
      Width = 81
      Height = 21
      ImeName = 'Microsoft IME 2010'
      ItemHeight = 13
      TabOrder = 11
      Text = 'ComboBillMoney'
      OnSelect = ComboDealSelect
    end
    object Billno: TEdit
      Left = 416
      Top = 124
      Width = 241
      Height = 21
      ImeName = 'Microsoft IME 2010'
      TabOrder = 12
    end
    object Billdt: TEdit
      Left = 80
      Top = 148
      Width = 97
      Height = 21
      ImeName = 'Microsoft IME 2010'
      TabOrder = 13
    end
    object billsn: TEdit
      Left = 256
      Top = 148
      Width = 81
      Height = 21
      ImeName = 'Microsoft IME 2010'
      TabOrder = 14
    end
    object billamt: TEdit
      Left = 416
      Top = 148
      Width = 81
      Height = 21
      ImeName = 'Microsoft IME 2010'
      TabOrder = 15
    end
    object Billserial: TEdit
      Left = 592
      Top = 148
      Width = 65
      Height = 21
      ImeName = 'Microsoft IME 2010'
      TabOrder = 16
    end
    object EditCashno: TEdit
      Left = 448
      Top = 72
      Width = 209
      Height = 21
      TabOrder = 17
    end
    object SignData: TEdit
      Left = 256
      Top = 96
      Width = 89
      Height = 21
      TabOrder = 18
    end
  end
  object EditAgreenum: TEdit
    Left = 280
    Top = 80
    Width = 81
    Height = 21
    ImeName = 'Microsoft IME 2010'
    TabOrder = 1
  end
  object GroupBox2: TGroupBox
    Left = 24
    Top = 232
    Width = 673
    Height = 177
    Caption = #49849#51064' '#51025#45813' DATA'
    TabOrder = 2
    object Label9: TLabel
      Left = 16
      Top = 56
      Width = 57
      Height = 13
      AutoSize = False
      Caption = #44144#47000#44396#48516
    end
    object Label10: TLabel
      Left = 16
      Top = 80
      Width = 49
      Height = 13
      AutoSize = False
      Caption = #48512#44032#49464
    end
    object Label11: TLabel
      Left = 16
      Top = 104
      Width = 57
      Height = 13
      AutoSize = False
      Caption = #49849#51064#51068#49884
    end
    object Label12: TLabel
      Left = 16
      Top = 128
      Width = 57
      Height = 13
      AutoSize = False
      Caption = #47588#51077#49324#47749
    end
    object Label13: TLabel
      Left = 16
      Top = 152
      Width = 65
      Height = 13
      AutoSize = False
      Caption = #51025#45813#47700#49884#51648
    end
    object Label14: TLabel
      Left = 184
      Top = 56
      Width = 57
      Height = 13
      AutoSize = False
      Caption = #44144#47000#50976#54805
    end
    object Label15: TLabel
      Left = 184
      Top = 80
      Width = 49
      Height = 13
      AutoSize = False
      Caption = #48393#49324#47308
    end
    object Label16: TLabel
      Left = 184
      Top = 104
      Width = 65
      Height = 13
      AutoSize = False
      Caption = #48156#44553#49324#53076#46300
    end
    object Label17: TLabel
      Left = 184
      Top = 128
      Width = 65
      Height = 13
      AutoSize = False
      Caption = #44032#47609#51216#48264#54840
    end
    object Label18: TLabel
      Left = 352
      Top = 56
      Width = 57
      Height = 13
      AutoSize = False
      Caption = #51025#45813#53076#46300
    end
    object Label19: TLabel
      Left = 376
      Top = 80
      Width = 22
      Height = 13
      Caption = #54624#48512
    end
    object Label20: TLabel
      Left = 352
      Top = 104
      Width = 57
      Height = 13
      AutoSize = False
      Caption = #48156#44553#49324#47749
    end
    object Label21: TLabel
      Left = 344
      Top = 128
      Width = 126
      Height = 13
      Caption = #49849#51064'CATID('#52636#44552#44032#45733#44552#50529')'
    end
    object Label22: TLabel
      Left = 296
      Top = 152
      Width = 112
      Height = 13
      Caption = #52852#46300'BIN('#52636#44552#44228#51340#48264#54840')'
    end
    object Label23: TLabel
      Left = 512
      Top = 56
      Width = 57
      Height = 13
      AutoSize = False
      Caption = #44144#47000#44552#50529
    end
    object Label24: TLabel
      Left = 512
      Top = 80
      Width = 57
      Height = 13
      AutoSize = False
      Caption = #49849#51064#48264#54840
    end
    object Label25: TLabel
      Left = 504
      Top = 104
      Width = 65
      Height = 13
      AutoSize = False
      Caption = #47588#51077#49324#53076#46300
    end
    object Label26: TLabel
      Left = 544
      Top = 128
      Width = 22
      Height = 13
      Caption = #51092#50529
    end
    object Label27: TLabel
      Left = 504
      Top = 152
      Width = 116
      Height = 13
      Caption = #52852#46300#44396#48516'('#50896#51109#51092#50529#48512#54840')'
    end
    object EditRecvdata: TEdit
      Left = 16
      Top = 24
      Width = 641
      Height = 21
      ImeName = 'Microsoft IME 2010'
      TabOrder = 0
    end
    object textBox17: TEdit
      Left = 88
      Top = 144
      Width = 209
      Height = 21
      ImeName = 'Microsoft IME 2010'
      TabOrder = 1
    end
    object textBox13: TEdit
      Left = 88
      Top = 120
      Width = 81
      Height = 21
      ImeName = 'Microsoft IME 2010'
      TabOrder = 2
    end
    object textBox9: TEdit
      Left = 88
      Top = 96
      Width = 81
      Height = 21
      ImeName = 'Microsoft IME 2010'
      TabOrder = 3
    end
    object textBox5: TEdit
      Left = 88
      Top = 72
      Width = 81
      Height = 21
      ImeName = 'Microsoft IME 2010'
      TabOrder = 4
    end
    object textBox1: TEdit
      Left = 88
      Top = 48
      Width = 81
      Height = 21
      ImeName = 'Microsoft IME 2010'
      TabOrder = 5
    end
    object textBox14: TEdit
      Left = 256
      Top = 120
      Width = 81
      Height = 21
      ImeName = 'Microsoft IME 2010'
      TabOrder = 6
    end
    object textBox10: TEdit
      Left = 256
      Top = 96
      Width = 81
      Height = 21
      ImeName = 'Microsoft IME 2010'
      TabOrder = 7
    end
    object textBox6: TEdit
      Left = 256
      Top = 72
      Width = 81
      Height = 21
      ImeName = 'Microsoft IME 2010'
      TabOrder = 8
    end
    object textBox2: TEdit
      Left = 256
      Top = 48
      Width = 81
      Height = 21
      ImeName = 'Microsoft IME 2010'
      TabOrder = 9
    end
    object textBox15: TEdit
      Left = 472
      Top = 120
      Width = 57
      Height = 21
      ImeName = 'Microsoft IME 2010'
      TabOrder = 10
    end
    object textBox18: TEdit
      Left = 416
      Top = 144
      Width = 81
      Height = 21
      ImeName = 'Microsoft IME 2010'
      TabOrder = 11
    end
    object textBox11: TEdit
      Left = 416
      Top = 96
      Width = 81
      Height = 21
      ImeName = 'Microsoft IME 2010'
      TabOrder = 12
    end
    object textBox7: TEdit
      Left = 416
      Top = 72
      Width = 81
      Height = 21
      ImeName = 'Microsoft IME 2010'
      TabOrder = 13
    end
    object textBox3: TEdit
      Left = 416
      Top = 48
      Width = 81
      Height = 21
      ImeName = 'Microsoft IME 2010'
      TabOrder = 14
    end
    object textBox12: TEdit
      Left = 576
      Top = 96
      Width = 81
      Height = 21
      ImeName = 'Microsoft IME 2010'
      TabOrder = 15
    end
    object textBox16: TEdit
      Left = 576
      Top = 120
      Width = 81
      Height = 21
      ImeName = 'Microsoft IME 2010'
      TabOrder = 16
    end
    object textBox8: TEdit
      Left = 576
      Top = 72
      Width = 81
      Height = 21
      ImeName = 'Microsoft IME 2010'
      TabOrder = 17
    end
    object textBox4: TEdit
      Left = 576
      Top = 48
      Width = 81
      Height = 21
      ImeName = 'Microsoft IME 2010'
      TabOrder = 18
    end
  end
  object textBox19: TEdit
    Left = 648
    Top = 376
    Width = 33
    Height = 21
    ImeName = 'Microsoft IME 2010'
    TabOrder = 3
  end
  object GroupBox3: TGroupBox
    Left = 24
    Top = 424
    Width = 673
    Height = 105
    Caption = #51204#47928' TEST'
    Font.Charset = DEFAULT_CHARSET
    Font.Color = clWindowText
    Font.Height = -11
    Font.Name = 'MS Sans Serif'
    Font.Style = []
    ParentFont = False
    TabOrder = 4
    object Label28: TLabel
      Left = 16
      Top = 24
      Width = 57
      Height = 13
      AutoSize = False
      Caption = #50836#52397#51204#47928
    end
    object Label29: TLabel
      Left = 16
      Top = 48
      Width = 57
      Height = 13
      AutoSize = False
      Caption = #51025#45813#51204#47928
    end
    object Label30: TLabel
      Left = 168
      Top = 76
      Width = 137
      Height = 13
      AutoSize = False
      Caption = #52852#46300#47532#45908' Reset '#45824#44592#49884#44036
    end
    object EditSend: TEdit
      Left = 88
      Top = 20
      Width = 569
      Height = 21
      ImeName = 'Microsoft IME 2010'
      TabOrder = 0
    end
    object EditRecv: TEdit
      Left = 88
      Top = 44
      Width = 569
      Height = 21
      ImeName = 'Microsoft IME 2010'
      TabOrder = 1
    end
    object ButtonNICEVCAT: TButton
      Left = 16
      Top = 72
      Width = 145
      Height = 21
      Caption = 'NICEVCAT'
      TabOrder = 2
      OnClick = ButtonNICEVCATClick
    end
    object ButtonRestart: TButton
      Left = 512
      Top = 72
      Width = 145
      Height = 21
      Caption = 'Restart'
      TabOrder = 3
      OnClick = ButtonRestartClick
    end
    object ButtonReset: TButton
      Left = 352
      Top = 72
      Width = 145
      Height = 21
      Caption = 'ReaderReset'
      TabOrder = 4
      OnClick = ButtonResetClick
    end
    object EditWaittime: TEdit
      Left = 312
      Top = 72
      Width = 25
      Height = 21
      ImeName = 'Microsoft IME 2010'
      TabOrder = 5
      Text = '5'
    end
  end
  object Button1: TButton
    Left = 24
    Top = 536
    Width = 257
    Height = 25
    Caption = 'CHK_CASHIC_MP ('#47680#54000#54056#46300' '#54788#44552'IC '#52852#46300#50668#48512' '#54869#51064')'
    TabOrder = 5
    OnClick = Button1Click
  end
  object Button2: TButton
    Left = 288
    Top = 536
    Width = 145
    Height = 25
    Caption = #47680#54000#54056#46300' IC'#52852#46300' '#54869#51064
    TabOrder = 6
    OnClick = Button2Click
  end
  object Button3: TButton
    Left = 440
    Top = 536
    Width = 177
    Height = 25
    Caption = 'REQ_BARCODE ('#48148#53076#46300'(QR)'#47532#46377')'
    TabOrder = 7
    OnClick = Button3Click
  end
  object Button4: TButton
    Left = 24
    Top = 568
    Width = 225
    Height = 25
    Caption = 'CHK_CASHIC2 ('#54788#44552'IC'#52852#46300#50668#48512#54869#51064')'
    Font.Charset = DEFAULT_CHARSET
    Font.Color = clWindowText
    Font.Height = -11
    Font.Name = 'MS Sans Serif'
    Font.Style = [fsBold]
    ParentFont = False
    TabOrder = 8
    OnClick = Button4Click
  end
  object Button5: TButton
    Left = 256
    Top = 568
    Width = 81
    Height = 25
    Caption = 'NVCAT '#51333#47308
    TabOrder = 9
    OnClick = Button5Click
  end
  object EditNiceDownYN: TEdit
    Left = 168
    Top = 600
    Width = 25
    Height = 21
    ImeName = 'Microsoft IME 2010'
    TabOrder = 10
    Text = 'T'
  end
  object EditCustomCnl: TEdit
    Left = 320
    Top = 600
    Width = 25
    Height = 21
    ImeName = 'Microsoft IME 2010'
    TabOrder = 11
    Text = 'N'
  end
  object Button6: TButton
    Left = 352
    Top = 600
    Width = 129
    Height = 25
    Caption = #48512#51221#52712#49548' '#49324#50857#50668#48512' '#49444#51221
    TabOrder = 12
    OnClick = Button6Click
  end
  object Button7: TButton
    Left = 488
    Top = 600
    Width = 81
    Height = 25
    Caption = 'Mac '#51452#49548' '#50619#44592
    TabOrder = 13
    OnClick = Button7Click
  end
  object Button8: TButton
    Left = 344
    Top = 568
    Width = 89
    Height = 25
    Caption = 'TDR '#49688#46041' LOCK'
    TabOrder = 14
    OnClick = Button8Click
  end
end
