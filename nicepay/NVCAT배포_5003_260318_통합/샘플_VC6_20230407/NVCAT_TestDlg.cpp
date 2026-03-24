// NVCAT_TestDlg.cpp : implementation file
//

#include "stdafx.h"
#include "NVCAT_Test.h"
#include "NVCAT_TestDlg.h"

#ifdef _DEBUG
#define new DEBUG_NEW
#undef THIS_FILE
static char THIS_FILE[] = __FILE__;
#endif

/////////////////////////////////////////////////////////////////////////////
// CNVCAT_TestDlg dialog

CNVCAT_TestDlg::CNVCAT_TestDlg(CWnd* pParent /*=NULL*/)
	: CDialog(CNVCAT_TestDlg::IDD, pParent)
{
	//{{AFX_DATA_INIT(CNVCAT_TestDlg)
	m_time = _T("5");
	m_Recvdata = _T("");
	m_DeviceType = _T("1");
	m_ServerIp = _T("10.222.141.105");
	m_ServerPort = _T("8101");
	m_CnlTestYn = _T("T");
	m_CnlUseYn = _T("N");
	m_FwFileDir = _T("DAISO_MP5000M_MPN033_v3223_220928_TMS.zip");
	m_ReaderType = _T("0");
	m_Halbu = _T("00");
	m_Money = _T("1004");
	m_Tax = _T("");
	m_Bongsa = _T("");
	m_Catid = _T("");
	m_ApprNo = _T("");
	m_ApprDt = _T("YYMMDD");
	m_CashKeyin = FALSE;
	m_CashTouch = FALSE;
	m_CashCard = FALSE;
	m_Barcode = _T("");
	m_CheckTp = _T("");
	m_CheckAmt = _T("");
	m_CheckDealNo = _T("");
	m_CheckDt = _T("");
	m_CheckMoney = _T("");
	m_CheckNo = _T("");
	m_CheckPersonNo = _T("");
	m_Txt = _T("HPS");
	m_Senddata = _T("");
	m_DealType = _T("10");
	m_DeviceTp = _T("");
	m_DealNo = _T("");
	m_Domain = _T("");
	m_IpAddress = _T("");
	//}}AFX_DATA_INIT
	m_hIcon = AfxGetApp()->LoadIcon(IDR_MAINFRAME);
}

void CNVCAT_TestDlg::DoDataExchange(CDataExchange* pDX)
{
	CDialog::DoDataExchange(pDX);
	//{{AFX_DATA_MAP(CNVCAT_TestDlg)
	DDX_Control(pDX, IDC_COMBO_CHECKAMT, m_cbCheckAmt);
	DDX_Control(pDX, IDC_COMBO_CHECKTP, m_cbCheckTp);
	DDX_Control(pDX, IDC_COMBO_DEALTP, m_DealTp);
	DDX_Text(pDX, IDC_EDIT29, m_time);
	DDX_Text(pDX, IDC_EDIT_RECVDATA, m_Recvdata);
	DDX_Text(pDX, IDC_EDIT99, m_DeviceType);
	DDX_Text(pDX, IDC_EDIT_SERVERIP, m_ServerIp);
	DDX_Text(pDX, IDC_EDIT_SERVERPORT, m_ServerPort);
	DDX_Text(pDX, IDC_EDIT_CNLTESTYN, m_CnlTestYn);
	DDX_Text(pDX, IDC_EDIT_CNLUSEYN, m_CnlUseYn);
	DDX_Text(pDX, IDC_EDIT_FWFILEDIR, m_FwFileDir);
	DDX_Text(pDX, IDC_EDIT_READERTYPE, m_ReaderType);
	DDX_CBString(pDX, IDC_COMBO_HALBU, m_Halbu);
	DDX_Text(pDX, IDC_EDIT_MONEY, m_Money);
	DDX_Text(pDX, IDC_EDIT_TAX, m_Tax);
	DDX_Text(pDX, IDC_EDIT_BONGSA, m_Bongsa);
	DDX_Text(pDX, IDC_EDIT_CATID, m_Catid);
	DDX_Text(pDX, IDC_EDIT_APPRNO, m_ApprNo);
	DDX_Text(pDX, IDC_EDIT_APPRDT, m_ApprDt);
	DDX_Check(pDX, IDC_CHECK2, m_CashKeyin);
	DDX_Check(pDX, IDC_CHECK3, m_CashTouch);
	DDX_Check(pDX, IDC_CHECK4, m_CashCard);
	DDX_Text(pDX, IDC_EDIT_BARCODE, m_Barcode);
	DDX_CBString(pDX, IDC_COMBO_CHECKTP, m_CheckTp);
	DDX_CBString(pDX, IDC_COMBO_CHECKAMT, m_CheckAmt);
	DDX_Text(pDX, IDC_EDIT_CHECKDEALNO, m_CheckDealNo);
	DDX_Text(pDX, IDC_EDIT_CHECKDT, m_CheckDt);
	DDX_Text(pDX, IDC_EDIT_CHECKMONEY, m_CheckMoney);
	DDX_Text(pDX, IDC_EDIT_CHECKNO, m_CheckNo);
	DDX_Text(pDX, IDC_EDIT_CHECKPERSONNO, m_CheckPersonNo);
	DDX_Text(pDX, IDC_EDIT_TXT, m_Txt);
	DDX_Text(pDX, IDC_EDIT_SENDDATA, m_Senddata);
	DDX_Text(pDX, IDC_EDIT_DEALTYPE, m_DealType);
	DDX_Text(pDX, IDC_EDIT_DEVICETP, m_DeviceTp);
	DDX_Text(pDX, IDC_EDIT_DEALNO, m_DealNo);
	DDX_Text(pDX, IDC_EDIT_DOMAIN, m_Domain);
	DDX_Text(pDX, IDC_EDIT_IPADDRESS, m_IpAddress);
	//}}AFX_DATA_MAP
}

BEGIN_MESSAGE_MAP(CNVCAT_TestDlg, CDialog)
	//{{AFX_MSG_MAP(CNVCAT_TestDlg)
	ON_WM_PAINT()
	ON_WM_QUERYDRAGICON()
	ON_BN_CLICKED(IDC_BUTTON1, OnButton1)
	ON_BN_CLICKED(IDC_BUTTON2, OnButton2)
	ON_BN_CLICKED(IDC_BUTTON3, OnButton3)
	ON_BN_CLICKED(IDC_BUTTON4, OnButton4)
	ON_BN_CLICKED(IDC_BUTTON5, OnButton5)
	ON_BN_CLICKED(IDC_BUTTON6, OnButton6)
	ON_BN_CLICKED(IDC_BUTTON7, OnButton7)
	ON_BN_CLICKED(IDC_BUTTON8, OnButton8)
	ON_BN_CLICKED(IDC_BUTTON9, OnButton9)
	ON_BN_CLICKED(IDC_BUTTON10, OnButton10)
	ON_BN_CLICKED(IDC_BUTTON11, OnButton11)
	ON_BN_CLICKED(IDC_BUTTON12, OnButton12)
	ON_BN_CLICKED(IDC_BUTTON13, OnButton13)
	ON_BN_CLICKED(IDC_BUTTON14, OnButton14)
	ON_BN_CLICKED(IDC_BUTTON15, OnButton15)
	ON_BN_CLICKED(IDC_BUTTON16, OnButton16)
	ON_BN_CLICKED(IDC_BUTTON17, OnButton17)
	ON_BN_CLICKED(IDC_BUTTON18, OnButton18)
	ON_BN_CLICKED(IDC_BUTTON19, OnButton19)
	ON_BN_CLICKED(IDC_BUTTON20, OnButton20)
	ON_BN_CLICKED(IDC_BUTTON21, OnButton21)
	ON_BN_CLICKED(IDC_BUTTON22, OnButton22)
	ON_BN_CLICKED(IDC_BUTTON23, OnButton23)
	ON_BN_CLICKED(IDC_BUTTON24, OnButton24)
	ON_BN_CLICKED(IDC_BUTTON25, OnButton25)
	ON_BN_CLICKED(IDC_BUTTON26, OnButton26)
	ON_BN_CLICKED(IDC_BUTTON27, OnButton27)
	//}}AFX_MSG_MAP
END_MESSAGE_MAP()

/////////////////////////////////////////////////////////////////////////////
// CNVCAT_TestDlg message handlers

BOOL CNVCAT_TestDlg::OnInitDialog()
{
	CDialog::OnInitDialog();

	SetIcon(m_hIcon, TRUE);			// Set big icon
	SetIcon(m_hIcon, FALSE);		// Set small icon
	
	// TODO: Add extra initialization here
	UpdateData(TRUE);

	m_DealTp.SetCurSel(0);
	CTime ctime = CTime::GetCurrentTime();
	m_ApprDt.Format("%04d%02d%02d", ctime.GetYear(), ctime.GetMonth(), ctime.GetDay());
	m_ApprDt = m_ApprDt.Mid(2, 6);
	m_cbCheckTp.SetCurSel(0);
	m_cbCheckAmt.SetCurSel(0);
	
	UpdateData(FALSE);

	return TRUE;  // return TRUE  unless you set the focus to a control
}

// If you add a minimize button to your dialog, you will need the code below
//  to draw the icon.  For MFC applications using the document/view model,
//  this is automatically done for you by the framework.

void CNVCAT_TestDlg::OnPaint() 
{
	if (IsIconic())
	{
		CPaintDC dc(this); // device context for painting

		SendMessage(WM_ICONERASEBKGND, (WPARAM) dc.GetSafeHdc(), 0);

		// Center icon in client rectangle
		int cxIcon = GetSystemMetrics(SM_CXICON);
		int cyIcon = GetSystemMetrics(SM_CYICON);
		CRect rect;
		GetClientRect(&rect);
		int x = (rect.Width() - cxIcon + 1) / 2;
		int y = (rect.Height() - cyIcon + 1) / 2;

		// Draw the icon
		dc.DrawIcon(x, y, m_hIcon);
	}
	else
	{
		CDialog::OnPaint();
	}
}

HCURSOR CNVCAT_TestDlg::OnQueryDragIcon()
{
	return (HCURSOR) m_hIcon;
}

void CNVCAT_TestDlg::OnButton1() 
{
	UpdateData(TRUE);

	typedef int (__stdcall *READER_RESET)(char *cWaitTime);
	READER_RESET	 lpREADER_RESET;
	
	HINSTANCE hDll = LoadLibrary("NVCAT.dll");
	if(hDll == NULL) {
		AfxMessageBox("NVCAT.dll Loading Error");
		return;
	}
	
	lpREADER_RESET = (READER_RESET)GetProcAddress(hDll, "READER_RESET");
	if(lpREADER_RESET == NULL) {
		AfxMessageBox("READER_RESET function Not found");
		return;
	}
	
	int ret = lpREADER_RESET(LPSTR(LPCTSTR(m_time)));
	
	CString cRet;
	cRet.Format(_T("리턴값 : %d"), ret);
	AfxMessageBox(cRet);

	UpdateData(FALSE);
}

void CNVCAT_TestDlg::OnButton2() 
{
	UpdateData(TRUE);

	typedef int (__stdcall *RESTART)();
	RESTART	 lpRESTART;
	
	HINSTANCE hDll = LoadLibrary("NVCAT.dll");
	if(hDll == NULL) {
		AfxMessageBox("NVCAT.dll Loading Error");
		return;
	}
	
	lpRESTART = (RESTART)GetProcAddress(hDll, "RESTART");
	if(lpRESTART == NULL) {
		AfxMessageBox("RESTART function Not found");
		return;
	}
	
	int ret = lpRESTART();
	
	CString cRet;
	cRet.Format(_T("리턴값 : %d"), ret);
	AfxMessageBox(cRet);

	
	UpdateData(FALSE);
}

void CNVCAT_TestDlg::OnButton3() 
{
	UpdateData(TRUE);

	typedef int (__stdcall *REQ_STOP)();
	REQ_STOP	 lpREQ_STOP;
	
	HINSTANCE hDll = LoadLibrary("NVCAT.dll");
	if(hDll == NULL) {
		AfxMessageBox("NVCAT.dll Loading Error");
		return;
	}
	
	lpREQ_STOP = (REQ_STOP)GetProcAddress(hDll, "REQ_STOP");
	if(lpREQ_STOP == NULL) {
		AfxMessageBox("REQ_STOP function Not found");
		return;
	}
	
	int ret = lpREQ_STOP();
	
	UpdateData(FALSE);
}

void CNVCAT_TestDlg::OnButton4() 
{
	UpdateData(TRUE);	

	typedef int (__stdcall *CHK_MEMBERSHIP)(char *recv_data);
	CHK_MEMBERSHIP	 lpCHK_MEMBERSHIP;
	
	HINSTANCE hDll = LoadLibrary("NVCAT.dll");
	if(hDll == NULL) {
		AfxMessageBox("NVCAT.dll Loading Error");
		return;
	}
	
	lpCHK_MEMBERSHIP = (CHK_MEMBERSHIP)GetProcAddress(hDll, "CHK_MEMBERSHIP");
	if(lpCHK_MEMBERSHIP == NULL) {
		AfxMessageBox("CHK_MEMBERSHIP function Not found");
		return;
	}
	
	char rbuf[2048];
	memset(rbuf, 0x00, sizeof(rbuf));

	int ret = lpCHK_MEMBERSHIP(rbuf);
	
	CString cRet;
	cRet.Format(_T("리턴값 : %d"), ret);
	AfxMessageBox(cRet);
	
	if(ret != 1) {
		AfxMessageBox("요청 실패! 리턴값이 1이 아닙니다.");
		return ;
	}

	m_Recvdata = rbuf;

	UpdateData(FALSE);
}

void CNVCAT_TestDlg::OnButton5() 
{
	UpdateData(TRUE);	
	
	typedef int (__stdcall *CHK_CARDBIN)(char *recv_data);
	CHK_CARDBIN	 lpCHK_CARDBIN;
	
	HINSTANCE hDll = LoadLibrary("NVCAT.dll");
	if(hDll == NULL) {
		AfxMessageBox("NVCAT.dll Loading Error");
		return;
	}
	
	lpCHK_CARDBIN = (CHK_CARDBIN)GetProcAddress(hDll, "CHK_CARDBIN");
	if(lpCHK_CARDBIN == NULL) {
		AfxMessageBox("CHK_CARDBIN function Not found");
		return;
	}
	
	char rbuf[2048];
	memset(rbuf, 0x00, sizeof(rbuf));
	
	int ret = lpCHK_CARDBIN(rbuf);
	
	CString cRet;
	cRet.Format(_T("리턴값 : %d"), ret);
	AfxMessageBox(cRet);
	
	if(ret != 1) {
		AfxMessageBox("요청 실패! 리턴값이 1이 아닙니다.");
		return ;
	}
	
	m_Recvdata = rbuf;
	
	UpdateData(FALSE);
}

void CNVCAT_TestDlg::OnButton6() 
{
	UpdateData(TRUE);
	
	typedef int (__stdcall *CHK_CARDIN)();
	CHK_CARDIN	 lpCHK_CARDIN;
	
	HINSTANCE hDll = LoadLibrary("NVCAT.dll");
	if(hDll == NULL) {
		AfxMessageBox("NVCAT.dll Loading Error");
		return;
	}
	
	lpCHK_CARDIN = (CHK_CARDIN)GetProcAddress(hDll, "CHK_CARDIN");
	if(lpCHK_CARDIN == NULL) {
		AfxMessageBox("CHK_CARDIN function Not found");
		return;
	}
	
	int ret = lpCHK_CARDIN();
	
	CString cRet;
	cRet.Format(_T("리턴값 : %d"), ret);
	AfxMessageBox(cRet);
	
	if(ret != 1) {
		AfxMessageBox("요청 실패! 리턴값이 1이 아닙니다.");
		return ;
	}
	
	UpdateData(FALSE);
}

void CNVCAT_TestDlg::OnButton7() 
{
	UpdateData(TRUE);
	
	typedef int (__stdcall *CHK_CARDIN_MP)();
	CHK_CARDIN_MP	 lpCHK_CARDIN_MP;
	
	HINSTANCE hDll = LoadLibrary("NVCAT.dll");
	if(hDll == NULL) {
		AfxMessageBox("NVCAT.dll Loading Error");
		return;
	}
	
	lpCHK_CARDIN_MP = (CHK_CARDIN_MP)GetProcAddress(hDll, "CHK_CARDIN_MP");
	if(lpCHK_CARDIN_MP == NULL) {
		AfxMessageBox("CHK_CARDIN_MP function Not found");
		return;
	}
	
	int ret = lpCHK_CARDIN_MP();
	
	CString cRet;
	cRet.Format(_T("리턴값 : %d"), ret);
	AfxMessageBox(cRet);
	
	if(ret != 1) {
		AfxMessageBox("요청 실패! 리턴값이 1이 아닙니다.");
		return ;
	}
	
	UpdateData(FALSE);
}

void CNVCAT_TestDlg::OnButton8() 
{
	UpdateData(TRUE);	
	
	typedef int (__stdcall *REQ_CASHNO)(char *recv_data);
	REQ_CASHNO	 lpREQ_CASHNO;
	
	HINSTANCE hDll = LoadLibrary("NVCAT.dll");
	if(hDll == NULL) {
		AfxMessageBox("NVCAT.dll Loading Error");
		return;
	}
	
	lpREQ_CASHNO = (REQ_CASHNO)GetProcAddress(hDll, "REQ_CASHNO");
	if(lpREQ_CASHNO == NULL) {
		AfxMessageBox("REQ_CASHNO function Not found");
		return;
	}
	
	char rbuf[2048];
	memset(rbuf, 0x00, sizeof(rbuf));
	
	int ret = lpREQ_CASHNO(rbuf);
	
	CString cRet;
	cRet.Format(_T("리턴값 : %d"), ret);
	AfxMessageBox(cRet);
	
	if(ret != 1) {
		AfxMessageBox("요청 실패! 리턴값이 1이 아닙니다.");
		return ;
	}
	
	m_Recvdata = rbuf;
	
	UpdateData(FALSE);
}

void CNVCAT_TestDlg::OnButton9() 
{
	UpdateData(TRUE);	
	
	AfxMessageBox("리더기/서명패드/터치스크린 유형 변경하시길 바랍니다.\n\(1 - 리더기, 2 - 서명패드\)");
	
	typedef int (__stdcall *REQ_BARCODE)(char *type, char *recv_data);
	REQ_BARCODE	 lpREQ_BARCODE;
	
	HINSTANCE hDll = LoadLibrary("NVCAT.dll");
	if(hDll == NULL) {
		AfxMessageBox("NVCAT.dll Loading Error");
		return;
	}
	
	lpREQ_BARCODE = (REQ_BARCODE)GetProcAddress(hDll, "REQ_BARCODE");
	if(lpREQ_BARCODE == NULL) {
		AfxMessageBox("REQ_BARCODE function Not found");
		return;
	}
	
	char rbuf[2048];
	memset(rbuf, 0x00, sizeof(rbuf));
	
	int ret = lpREQ_BARCODE(LPSTR(LPCTSTR(m_DeviceType)), rbuf); //TYPE : "0"(리더기), "1"(서명패드)
	
	CString cRet;
	cRet.Format(_T("리턴값 : %d"), ret);
	AfxMessageBox(cRet);
	
	if(ret != 1) {
		AfxMessageBox("요청 실패! 리턴값이 1이 아닙니다.");
		return ;
	}
	
	m_Recvdata = rbuf;
	
	UpdateData(FALSE);
}

void CNVCAT_TestDlg::OnButton10() 
{
	UpdateData(TRUE);	
	
	typedef int (__stdcall *REQ_SIGNDATA)(char *recv_data);
	REQ_SIGNDATA	 lpREQ_SIGNDATA;
	
	HINSTANCE hDll = LoadLibrary("NVCAT.dll");
	if(hDll == NULL) {
		AfxMessageBox("NVCAT.dll Loading Error");
		return;
	}
	
	lpREQ_SIGNDATA = (REQ_SIGNDATA)GetProcAddress(hDll, "REQ_SIGNDATA");
	if(lpREQ_SIGNDATA == NULL) {
		AfxMessageBox("REQ_SIGNDATA function Not found");
		return;
	}
	
	char rbuf[2048];
	memset(rbuf, 0x00, sizeof(rbuf));
	
	int ret = lpREQ_SIGNDATA(rbuf);
	
	CString cRet;
	cRet.Format(_T("리턴값 : %d"), ret);
	AfxMessageBox(cRet);

	if(ret != 1) {
		AfxMessageBox("요청 실패! 리턴값이 1이 아닙니다.");
		return ;
	}
	
	m_Recvdata = rbuf;
	
	UpdateData(FALSE);
}

void CNVCAT_TestDlg::OnButton11() 
{
	UpdateData(TRUE);	
	
	typedef int (__stdcall *Set_SvrInfo)(char *IP, char *PORT);
	Set_SvrInfo	 lpSet_SvrInfo;
	
	HINSTANCE hDll = LoadLibrary("NVCAT.dll");
	if(hDll == NULL) {
		AfxMessageBox("NVCAT.dll Loading Error");
		return;
	}
	
	lpSet_SvrInfo = (Set_SvrInfo)GetProcAddress(hDll, "Set_SvrInfo");
	if(lpSet_SvrInfo == NULL) {
		AfxMessageBox("Set_SvrInfo function Not found");
		return;
	}
	
	int ret = lpSet_SvrInfo(LPSTR(LPCTSTR(m_ServerIp)), LPSTR(LPCTSTR(m_ServerPort)));
	
	if(ret != 1) {
		AfxMessageBox("리턴 값이 1이 아닙니다.");
		return ;
	}
	
	UpdateData(FALSE);
}

void CNVCAT_TestDlg::OnButton12() 
{
	UpdateData(TRUE);
	
	typedef int (__stdcall *NVCATSHUTDOWN)();
	NVCATSHUTDOWN	 lpNVCATSHUTDOWN;
	
	HINSTANCE hDll = LoadLibrary("NVCAT.dll");
	if(hDll == NULL) {
		AfxMessageBox("NVCAT.dll Loading Error");
		return;
	}
	
	lpNVCATSHUTDOWN = (NVCATSHUTDOWN)GetProcAddress(hDll, "NVCATSHUTDOWN");
	if(lpNVCATSHUTDOWN == NULL) {
		AfxMessageBox("NVCATSHUTDOWN function Not found");
		return;
	}
	
	int ret = lpNVCATSHUTDOWN();
	
	CString cRet;
	cRet.Format(_T("리턴값 : %d"), ret);
	AfxMessageBox(cRet);

	UpdateData(FALSE);
}

void CNVCAT_TestDlg::OnButton13() 
{
	UpdateData(TRUE);
	
	typedef int (__stdcall *CHK_CASHIC_MP2)();
	CHK_CASHIC_MP2	 lpCHK_CASHIC_MP2;
	
	HINSTANCE hDll = LoadLibrary("NVCAT.dll");
	if(hDll == NULL) {
		AfxMessageBox("NVCAT.dll Loading Error");
		return;
	}
	
	lpCHK_CASHIC_MP2 = (CHK_CASHIC_MP2)GetProcAddress(hDll, "CHK_CASHIC_MP2");
	if(lpCHK_CASHIC_MP2 == NULL) {
		AfxMessageBox("CHK_CASHIC_MP2 function Not found");
		return;
	}
	
	int ret = lpCHK_CASHIC_MP2();
	
	CString cRet;
	cRet.Format(_T("리턴값 : %d"), ret);
	AfxMessageBox(cRet);
	
	if(ret != 1) {
		AfxMessageBox("요청 실패! 리턴값이 1이 아닙니다.");
		return ;
	}
	
	UpdateData(FALSE);
}

void CNVCAT_TestDlg::OnButton14() 
{
	UpdateData(TRUE);	
	
	typedef int (__stdcall *SetCnlDisableYN)(char *dn_tp, char *disable_tp);
	SetCnlDisableYN	 lpSetCnlDisableYN;
	
	HINSTANCE hDll = LoadLibrary("NVCAT.dll");
	if(hDll == NULL) {
		AfxMessageBox("NVCAT.dll Loading Error");
		return;
	}
	
	lpSetCnlDisableYN = (SetCnlDisableYN)GetProcAddress(hDll, "SetCnlDisableYN");
	if(lpSetCnlDisableYN == NULL) {
		AfxMessageBox("SetCnlDisableYN function Not found");
		return;
	}
	
	int ret = lpSetCnlDisableYN(LPSTR(LPCTSTR(m_CnlTestYn)), LPSTR(LPCTSTR(m_CnlUseYn)));
	
	if(ret != 1) {
		AfxMessageBox("리턴 값이 1이 아닙니다.");
		return ;
	}
	
	UpdateData(FALSE);
}

void CNVCAT_TestDlg::OnButton15() 
{
	UpdateData(TRUE);
	
	typedef int (__stdcall *REQ_TITLOCK)();
	REQ_TITLOCK	 lpREQ_TITLOCK;
	
	HINSTANCE hDll = LoadLibrary("NVCAT.dll");
	if(hDll == NULL) {
		AfxMessageBox("NVCAT.dll Loading Error");
		return;
	}
	
	lpREQ_TITLOCK = (REQ_TITLOCK)GetProcAddress(hDll, "REQ_TITLOCK");
	if(lpREQ_TITLOCK == NULL) {
		AfxMessageBox("REQ_TITLOCK function Not found");
		return;
	}
	
	int ret = lpREQ_TITLOCK();
	
	CString cRet;
	cRet.Format(_T("리턴값 : %d"), ret);
	AfxMessageBox(cRet);
	
	if(ret != 1) {
		AfxMessageBox("요청 실패! 리턴값이 1이 아닙니다.");
		return ;
	}
	
	UpdateData(FALSE);	
}

void CNVCAT_TestDlg::OnButton16() 
{
	UpdateData(TRUE);	
	
	AfxMessageBox("리더기/서명패드/터치스크린 유형 변경하시길 바랍니다.\n\(1 - 서명패드, 2 - 터치스크린\)");
	
	typedef int (__stdcall *REQ_SELECTBTN)(char *type, char *send_data, char *recv_data);
	REQ_SELECTBTN	 lpREQ_SELECTBTN;
	
	HINSTANCE hDll = LoadLibrary("NVCAT.dll");
	if(hDll == NULL) {
		AfxMessageBox("NVCAT.dll Loading Error");
		return;
	}
	
	lpREQ_SELECTBTN = (REQ_SELECTBTN)GetProcAddress(hDll, "REQ_SELECTBTN");
	if(lpREQ_SELECTBTN == NULL) {
		AfxMessageBox("REQ_SELECTBTN function Not found");
		return;
	}
	
	char rbuf[2048];
	memset(rbuf, 0x00, sizeof(rbuf));

	int ret = lpREQ_SELECTBTN(LPSTR(LPCTSTR(m_DeviceType)), "현금IC 거래를 하시겠습니까?", rbuf); //"1" : 서명패드, "2" 터치스크린으로 요청
	
	CString cRet;
	cRet.Format(_T("리턴값 : %d"), ret);
	AfxMessageBox(cRet);
	
	if(ret != 1) {
		AfxMessageBox("요청 실패! 리턴값이 1이 아닙니다.");
		return ;
	}
	
	m_Recvdata = rbuf;

	UpdateData(FALSE);
}

void CNVCAT_TestDlg::OnButton17() 
{
	UpdateData(TRUE);	
	
	AfxMessageBox("리더기/서명패드/터치스크린 유형 변경하시길 바랍니다.\n\(1 - 리더기, 2 - 서명패드\)");

	typedef int (__stdcall *REQ_BALANCE)(char *type, char *recv_data);
	REQ_BALANCE	 lpREQ_BALANCE;
	
	HINSTANCE hDll = LoadLibrary("NVCAT.dll");
	if(hDll == NULL) {
		AfxMessageBox("NVCAT.dll Loading Error");
		return;
	}
	
	lpREQ_BALANCE = (REQ_BALANCE)GetProcAddress(hDll, "REQ_BALANCE");
	if(lpREQ_BALANCE == NULL) {
		AfxMessageBox("REQ_BALANCE function Not found");
		return;
	}
	
	char rbuf[2048];
	memset(rbuf, 0x00, sizeof(rbuf));
	
	int ret = lpREQ_BALANCE(LPSTR(LPCTSTR(m_DeviceType)), rbuf);
	
	CString cRet;
	cRet.Format(_T("리턴값 : %d"), ret);
	AfxMessageBox(cRet);
	
	if(ret != 1) {
		AfxMessageBox("요청 실패! 리턴값이 1이 아닙니다.");
		return ;
	}
	
	m_Recvdata = rbuf;
	
	UpdateData(FALSE);
}

void CNVCAT_TestDlg::OnButton18() 
{
	UpdateData(TRUE);
	
	typedef int (__stdcall *CHK_CARDIN_TIT)();
	CHK_CARDIN_TIT	 lpCHK_CARDIN_TIT;
	
	HINSTANCE hDll = LoadLibrary("NVCAT.dll");
	if(hDll == NULL) {
		AfxMessageBox("NVCAT.dll Loading Error");
		return;
	}
	
	lpCHK_CARDIN_TIT = (CHK_CARDIN_TIT)GetProcAddress(hDll, "CHK_CARDIN_TIT");
	if(lpCHK_CARDIN_TIT == NULL) {
		AfxMessageBox("CHK_CARDIN_TIT function Not found");
		return;
	}
	
	int ret = lpCHK_CARDIN_TIT();
	
	CString cRet;
	cRet.Format(_T("리턴값 : %d"), ret);
	AfxMessageBox(cRet);
	
	if(ret != 1) {
		AfxMessageBox("요청 실패! 리턴값이 1이 아닙니다.");
		return ;
	}
	
	UpdateData(FALSE);	
}

void CNVCAT_TestDlg::OnButton19() 
{
	UpdateData(TRUE);	
	
	typedef int (__stdcall *REQ_FW_UPDATE)(long readertype, char *fwfilepath);
	REQ_FW_UPDATE	 lpREQ_FW_UPDATE;
	
	HINSTANCE hDll = LoadLibrary("NVCAT.dll");
	if(hDll == NULL) {
		AfxMessageBox("NVCAT.dll Loading Error");
		return;
	}
	
	lpREQ_FW_UPDATE = (REQ_FW_UPDATE)GetProcAddress(hDll, "REQ_FW_UPDATE");
	if(lpREQ_FW_UPDATE == NULL) {
		AfxMessageBox("REQ_FW_UPDATE function Not found");
		return;
	}
	
	int ret = lpREQ_FW_UPDATE(_ttoi(m_ReaderType), LPSTR(LPCTSTR(m_FwFileDir)));
	
	if(ret != 1) {
		AfxMessageBox("리턴 값이 1이 아닙니다.");
		return ;
	}
	
	UpdateData(FALSE);
}

void CNVCAT_TestDlg::OnButton20() 
{
	UpdateData(TRUE);
	
	typedef int (__stdcall *CHK_CASHIC2)();
	CHK_CASHIC2	 lpCHK_CASHIC2;
	
	HINSTANCE hDll = LoadLibrary("NVCAT.dll");
	if(hDll == NULL) {
		AfxMessageBox("NVCAT.dll Loading Error");
		return;
	}
	
	lpCHK_CASHIC2 = (CHK_CASHIC2)GetProcAddress(hDll, "CHK_CASHIC2");
	if(lpCHK_CASHIC2 == NULL) {
		AfxMessageBox("CHK_CASHIC2 function Not found");
		return;
	}
	
	int ret = lpCHK_CASHIC2();
	
	CString cRet;
	cRet.Format(_T("리턴값 : %d"), ret);
	AfxMessageBox(cRet);
	
	if(ret != 1) {
		AfxMessageBox("요청 실패! 리턴값이 1이 아닙니다.");
		return ;
	}
	
	UpdateData(FALSE);	
}

void CNVCAT_TestDlg::OnButton21() 
{
	UpdateData(TRUE);
	
	typedef int (__stdcall *READER_RESET)(char *cWaitTime);
	READER_RESET	 lpREADER_RESET;
	
	HINSTANCE hDll = LoadLibrary("NVCAT.dll");
	if(hDll == NULL) {
		AfxMessageBox("NVCAT.dll Loading Error");
		return;
	}
	
	lpREADER_RESET = (READER_RESET)GetProcAddress(hDll, "READER_RESET");
	if(lpREADER_RESET == NULL) {
		AfxMessageBox("READER_RESET function Not found");
		return;
	}
	
	int ret = lpREADER_RESET("0");
	
	CString cRet;
	cRet.Format(_T("리턴값 : %d"), ret);
	AfxMessageBox(cRet);
	
	UpdateData(FALSE);	
}

void CNVCAT_TestDlg::OnButton22() 
{
	UpdateData(TRUE);	
	
	char FS = 0x1C;
	char sbuf[4096], rbuf[4096];
	memset(sbuf, 0x00, sizeof(sbuf));
	memset(rbuf, 0x00, sizeof(rbuf));
	
	int opt = m_DealTp.GetCurSel();
	
	char cHalbu[16];
	memset(cHalbu, 0x00, sizeof(cHalbu));
	sprintf(cHalbu, "%02d", atoi(m_Halbu));
	
	CString m_SignPadDisplay = "";

	switch(opt)
	{
	case 0: //신용승인
		sprintf(sbuf, "0200%c10%cC%c%s%c%s%c%s%c%s%c%c%c%s%c%c%c%c%c%c%c%cFiller%c", FS, FS, FS, m_Money, FS, m_Tax, FS, m_Bongsa, FS, m_Halbu, FS, FS, FS, m_Catid, FS, FS, FS, FS, FS, FS, FS, FS, FS);
		break;
	case 1: //FALLBACK
		sprintf(sbuf, "0200%c10%cF%c%s%c%s%c%s%c%s%c%c%c%s%c%c%c%c%c%c%c%cFiller%c", FS, FS, FS, m_Money, FS, m_Tax, FS, m_Bongsa, FS, m_Halbu, FS, FS, FS, m_Catid, FS, FS, FS, FS, FS, FS, FS, FS, FS);
		break;
	case 2: //신용취소
		sprintf(sbuf, "0420%c10%cC%c%s%c%s%c%s%c%s%c%s%c%s%c%s%c%c%c%c%c%c%c%cFiller%c", FS, FS, FS, m_Money, FS, m_Tax, FS, m_Bongsa, FS, m_Halbu, FS, m_ApprNo, FS, m_ApprDt, FS, m_Catid, FS, FS, FS, FS, FS, FS, FS, FS, FS);
		break;
	case 3: //현금승인
		if(m_CashKeyin) 
			sprintf(sbuf, "0200%c21%cK%c%s%c%s%c%s%c%s%c%c%c%s%c%c%c%c%c%c%c%cFiller%c", FS, FS, FS, m_Money, FS, m_Tax, FS, m_Bongsa, FS, m_Halbu, FS, FS, FS, m_Catid, FS, FS, FS, FS, FS, FS, FS, FS, FS);        
		else if(m_CashTouch)
			sprintf(sbuf, "0200%c21%cT%c%s%c%s%c%s%c%s%c%c%c%s%c%c%c%c%c%c%c%cFiller%c", FS, FS, FS, m_Money, FS, m_Tax, FS, m_Bongsa, FS, m_Halbu, FS, FS, FS, m_Catid, FS, FS, FS, FS, FS, FS, FS, FS, FS);        
		else if(m_CashCard)
			sprintf(sbuf, "0200%c21%cC%c%s%c%s%c%s%c%s%c%c%c%s%c%c%c%c%c%c%c%cFiller%c", FS, FS, FS, m_Money, FS, m_Tax, FS, m_Bongsa, FS, m_Halbu, FS, FS, FS, m_Catid, FS, FS, FS, FS, FS, FS, FS, FS, FS);        
		else 
			sprintf(sbuf, "0200%c21%cP%c%s%c%s%c%s%c%s%c%c%c%s%c%c%c%s%c%c%c%c%cFiller%c", FS, FS, FS, m_Money, FS, m_Tax, FS, m_Bongsa, FS, m_Halbu, FS, FS, FS, m_Catid, FS, FS, FS, m_Barcode, FS, FS, FS, FS, FS, FS);        
		break;
	case 4: //현금취소
		if(m_CashKeyin) 
			sprintf(sbuf, "0420%c21%cK%c%s%c%s%c%s%c%s%c%s%c%s%c%s%c%c%c%c%c%c%c%cFiller%c", FS, FS, FS, m_Money, FS, m_Tax, FS, m_Bongsa, FS, m_Halbu, FS, m_ApprNo, FS, m_ApprDt, FS, m_Catid, FS, FS, FS, FS, FS, FS, FS, FS, FS);        
		else if(m_CashTouch)
			sprintf(sbuf, "0420%c21%cT%c%s%c%s%c%s%c%s%c%s%c%s%c%s%c%c%c%c%c%c%c%cFiller%c", FS, FS, FS, m_Money, FS, m_Tax, FS, m_Bongsa, FS, m_Halbu, FS, m_ApprNo, FS, m_ApprDt, FS, m_Catid, FS, FS, FS, FS, FS, FS, FS, FS, FS);        
		else if(m_CashCard)
			sprintf(sbuf, "0420%c21%cC%c%s%c%s%c%s%c%s%c%s%c%s%c%s%c%c%c%c%c%c%c%cFiller%c", FS, FS, FS, m_Money, FS, m_Tax, FS, m_Bongsa, FS, m_Halbu, FS, m_ApprNo, FS, m_ApprDt, FS, m_Catid, FS, FS, FS, FS, FS, FS, FS, FS, FS);        
		else 
			sprintf(sbuf, "0420%c21%cP%c%s%c%s%c%s%c%s%c%s%c%s%c%s%c%c%c%s%c%c%c%c%cFiller%c", FS, FS, FS, m_Money, FS, m_Tax, FS, m_Bongsa, FS, m_Halbu, FS, m_ApprNo, FS, m_ApprDt, FS, m_Catid, FS, FS, FS, m_Barcode, FS, FS, FS, FS, FS, FS);        
		break;
	case 5: //은련승인
		sprintf(sbuf, "0200%cUP%cC%c%s%c%s%c%s%c%s%c%c%c%s%c%c%c%c%c%c%c%cFiller%c", FS, FS, FS, m_Money, FS, m_Tax, FS, m_Bongsa, FS, m_Halbu, FS, FS, FS, m_Catid, FS, FS, FS, FS, FS, FS, FS, FS, FS);
		break;
	case 6: //은련취소
		sprintf(sbuf, "0420%cUP%cC%c%s%c%s%c%s%c%s%c%s%c%s%c%s%c%c%c%c%c%c%c%cFiller%c", FS, FS, FS, m_Money, FS, m_Tax, FS, m_Bongsa, FS, m_Halbu, FS, m_ApprNo, FS, m_ApprDt, FS, m_Catid, FS, FS, FS, FS, FS, FS, FS, FS, FS);
		break;
	case 7: //수표조회
		char mbilltp[256], mbillamt[256];
		memset(mbilltp, 0x00, sizeof(mbilltp));
		memset(mbillamt, 0x00, sizeof(mbillamt));
		sprintf(mbilltp, "%s", m_CheckTp.Mid(0, 2));
		sprintf(mbillamt, "%s", m_CheckAmt.Mid(0, 2));
		
		sprintf(sbuf, "0200%c20%cK%c%s%c%s%c%s%c%s%c%s%c%s%c%s%c%c%c%c%c%c%c", FS, FS, FS, mbilltp, FS, mbillamt, FS, m_CheckNo, FS, m_CheckDt, FS, m_CheckPersonNo, FS, m_CheckMoney, FS, m_CheckDealNo, FS, FS, FS, FS, FS, FS, FS);
		break;
	case 8: //현금IC 승인 (간소화)
		sprintf(sbuf, "0200%cI1%c01%c%s%c%s%c%s%c%c%c%s%c%c%c%cFiller%c%c%c%c%c%c", FS, FS, FS, m_Bongsa, FS, m_Tax, FS, m_Money, FS, FS, FS, m_Catid, FS, FS, FS, FS, FS, FS, FS, FS, FS, FS);
		break;
	case 9: //현금IC 취소 (간소화)
		sprintf(sbuf, "0420%cI4%c01%c%s%c%s%c%s%c%s%c%s%c%s%c%c%c%cFiller%c%c%c%c%c%c", FS, FS, FS, m_Bongsa, FS, m_Tax, FS, m_Money, FS, m_ApprNo, FS, m_ApprDt, FS, m_Catid, FS, FS, FS, FS, FS, FS, FS, FS, FS, FS);
		break;
	case 10: //신용무카드취소 (일련번호)
		sprintf(sbuf, "0420%c10%cN%c%s%c%s%c%s%c%s%c%s%c%s%c%s%c%c%c%s%c%c%c%c%cFiller%c", FS, FS, FS, m_Money, FS, m_Tax, FS, m_Bongsa, FS, m_Halbu, FS, m_ApprNo, FS, m_ApprDt, FS, m_Catid, FS, FS, FS, m_Barcode, FS, FS, FS, FS, FS, FS);
		break;
	case 11: //신용무카드부분취소 (일련번호) (원거래 금액 : 1004)
		sprintf(sbuf, "0520%c30%cN%c%s%c%s%c%s%c%s%c%s%c%s%c%s%c%c%c%s%c%c%c%c%cFiller%cP000000001004%cPCL%c%c%c%c%c%c", FS, FS, FS, m_Money, FS, m_Tax, FS, m_Bongsa, FS, m_Halbu, FS, m_ApprNo, FS, m_ApprDt, FS, m_Catid, FS, FS, FS, m_Barcode, FS, FS, FS, FS, FS, FS, FS, FS, FS, FS, FS, FS, FS);
		break;
	case 12: //현금무카드취소
		sprintf(sbuf, "0420%c21%cN%c%s%c%s%c%s%c%s%c%s%c%s%c%s%c%c%c%c%c%c%c%cFiller%c", FS, FS, FS, m_Money, FS, m_Tax, FS, m_Bongsa, FS, m_Halbu, FS, m_ApprNo, FS, m_ApprDt, FS, m_Catid, FS, FS, FS, FS, FS, FS, FS, FS, FS);
		break;
	case 13: //현금IC무카드취소
		sprintf(sbuf, "0420%cI4%c02%c%s%c%s%c%s%c%s%c%s%c%s%c%c%c%cFiller%c%c%c%c%c%c", FS, FS, FS, m_Bongsa, FS, m_Tax, FS, m_Money, FS, m_ApprNo, FS, m_ApprDt, FS, m_Catid, FS, FS, FS, FS, FS, FS, FS, FS, FS, FS);
		break;
	case 14: //DCC 승인 (NVCAT 2TR)
		sprintf(sbuf, "0200%cDC%cC%c%s%c%s%c%s%c%s%c%c%c%s%c410%c%s%c0%c%c%c%c%cFiller%c%c%c", FS, FS, FS, m_Money, FS, m_Tax, FS, m_Bongsa, FS, m_Halbu, FS, FS, FS, m_Catid, FS, FS, m_Money, FS, FS, FS, FS, FS, FS, FS, FS, FS);
		break;
	case 15: //포인트 승인 
		sprintf(sbuf, "0300%c%s%cI%c%s%c%s%c%s%c%s%c%c%c%s%c%c%c%c%c%c%c%cFiller%c%c%s%c%s%c%s%c%s%c%s%c%c", FS, m_DealType, FS, FS, m_Money, FS, m_Tax, FS, m_Bongsa, FS, m_Halbu, FS, FS, FS, m_Catid, FS, FS, FS, FS, FS, FS, FS, FS, FS, FS, m_Txt, FS, m_DeviceTp, FS, m_DealNo, FS, m_Domain, FS, m_IpAddress, FS, FS);
		break;
	case 16: //포인트 취소
		sprintf(sbuf, "0520%c%s%cI%c%s%c%s%c%s%c%s%c%s%c%s%c%s%c%c%c%c%c%c%c%cFiller%c%c%s%c%s%c%s%c%s%c%s%c%c", FS, m_DealType, FS, FS, m_Money, FS, m_Tax, FS, m_Bongsa, FS, m_Halbu, FS, m_ApprNo, FS, m_ApprDt, FS, m_Catid, FS, FS, FS, FS, FS, FS, FS, FS, FS, FS, m_Txt, FS, m_DeviceTp, FS, m_DealNo, FS, m_Domain, FS, m_IpAddress, FS, FS);
		break;
	case 17: //멤버쉽 승인
		AfxMessageBox("부가세 - 적립구분\n봉사료 - 포인트구분\n고객식별번호 - 비밀번호\n셋팅해주시길 바랍니다!");
		sprintf(sbuf, "0320%c%s%cI%c%s%c%s%c%s%c%s%c%c%c%s%c%c%c%c%c%c%c%cFiller%c%c%s%c%s%c%c%c%c", FS, m_DealType, FS, FS, m_Money, FS, m_Tax, FS, m_Bongsa, FS, m_Barcode, FS, FS, FS, m_Catid, FS, FS, FS, FS, FS, FS, FS, FS, FS, FS, m_Txt, FS, m_DeviceTp, FS, FS, FS, FS);
		break;
	case 18: //멤버쉽 취소
		AfxMessageBox("부가세 - 적립구분\n봉사료 - 포인트구분\n고객식별번호 - 비밀번호\n셋팅해주시길 바랍니다!");
		sprintf(sbuf, "0540%c%s%cI%c%s%c%s%c%s%c%s%c%s%c%s%c%s%c%c%c%c%c%c%c%cFiller%c%c%s%c%s%c%c%c%c", FS, m_DealType, FS, FS, m_Money, FS, m_Tax, FS, m_Bongsa, FS, m_Barcode, FS, m_ApprNo, FS, m_ApprDt, FS, m_Catid, FS, FS, FS, FS, FS, FS, FS, FS, FS, FS, m_Txt, FS, m_DeviceTp, FS, FS, FS, FS);
		break;
	case 19: //SKP토큰발행(S1)
		m_SignPadDisplay = "19881130100"; //서명패드표시금액 : 실소유자생년월일/성별(9)+카드비밀번호2자리(2) 
		m_Barcode = ""; //토큰번호
		m_DealType = "S1"; //거래유형
		m_Txt = "HPS"; //전문TEXT
		m_DeviceTp = "H1"; //기종구분
		m_Domain = "USERID12345678901234이주용"; //도메인 : 가맹점UserID(병록번호)(20)+실소유자명(10)
		m_IpAddress = "   01023720000SKT"; //IP ADDRESS : 국내/해외카드구분자(3)+휴대폰번호(11)+휴대폰통신사(4)
		sprintf(sbuf, "0300%c%s%cL%c%s%c%s%c%s%c%s%c%c%c%s%c%c%c%s%c%c%c%c%cFiller%c%s%c%s%c%s%c%c%s%c%s%c%c", FS, m_DealType, FS, FS, m_Money, FS, m_Tax, FS, m_Bongsa, FS, m_Halbu, FS, FS, FS, m_Catid, FS, FS, FS, m_Barcode, FS, FS, FS, FS, FS, FS, m_SignPadDisplay, FS, m_Txt, FS, m_DeviceTp, FS, FS, m_Domain, FS, m_IpAddress, FS, FS);
		break;
	case 20: //SKP토큰승인(S2)
		m_SignPadDisplay = ""; //서명패드표시금액
		//m_Barcode = ""; //토큰번호 (입력 필요)
		m_DealType = "S2"; //거래유형
		m_Txt = "HPS"; //전문TEXT
		m_DeviceTp = "H1"; //기종구분
		m_Domain = ""; //도메인
		m_IpAddress = ""; //IP ADDRESSSpace(15)
		sprintf(sbuf, "0300%c%s%cL%c%s%c%s%c%s%c%s%c%c%c%s%c%c%c%s%c%c%c%c%cFiller%c%s%c%s%c%s%c%c%s%c%s%c%c", FS, m_DealType, FS, FS, m_Money, FS, m_Tax, FS, m_Bongsa, FS, m_Halbu, FS, FS, FS, m_Catid, FS, FS, FS, m_Barcode, FS, FS, FS, FS, FS, FS, m_SignPadDisplay, FS, m_Txt, FS, m_DeviceTp, FS, FS, m_Domain, FS, m_IpAddress, FS, FS);
		break;
	case 21: //SKP토큰취소(S2)
		m_SignPadDisplay = ""; //서명패드표시금액
		//m_Barcode = ""; //토큰번호 (입력 필요)
		m_DealType = "S2"; //거래유형
		m_Txt = "HPS"; //전문TEXT
		m_DeviceTp = "H1"; //기종구분
		m_Domain = ""; //도메인
		m_IpAddress = ""; //IP ADDRESSSpace(15)
		sprintf(sbuf, "0520%c%s%cL%c%s%c%s%c%s%c%s%c%s%c%s%c%s%c%c%c%s%c%c%c%c%cFiller%c%s%c%s%c%s%c%c%s%c%s%c%c", FS, m_DealType, FS, FS, m_Money, FS, m_Tax, FS, m_Bongsa, FS, m_Halbu, FS, m_ApprNo, FS, m_ApprDt, FS, m_Catid, FS, FS, FS, m_Barcode, FS, FS, FS, FS, FS, FS, m_SignPadDisplay, FS, m_Txt, FS, m_DeviceTp, FS, FS, m_Domain, FS, m_IpAddress, FS, FS);
		break;
	case 22: //SKP토큰삭제(S3)
		m_SignPadDisplay = ""; //서명패드표시금액
		//m_Barcode = ""; //토큰번호 (입력 필요)
		m_DealType = "S3"; //거래유형
		m_Txt = "HPS"; //전문TEXT
		m_DeviceTp = "H1"; //기종구분
		m_Domain = "USERID12345678901234이주용"; //도메인 : 가맹점UserID(병록번호)(20)+실소유자명(10)
		m_IpAddress = ""; //IP ADDRESSSpace(15)
		sprintf(sbuf, "0300%c%s%cL%c%s%c%s%c%s%c%s%c%c%c%s%c%c%c%s%c%c%c%c%cFiller%c%s%c%s%c%s%c%c%s%c%s%c%c", FS, m_DealType, FS, FS, m_Money, FS, m_Tax, FS, m_Bongsa, FS, m_Halbu, FS, FS, FS, m_Catid, FS, FS, FS, m_Barcode, FS, FS, FS, FS, FS, FS, m_SignPadDisplay, FS, m_Txt, FS, m_DeviceTp, FS, FS, m_Domain, FS, m_IpAddress, FS, FS);
		break;
	default: //추후 개발 필요
		AfxMessageBox("개발 필요합니다.");
		break;
	}
	
	typedef int (__stdcall *NICEVCAT)(char *send_data, char *recv_data);
	NICEVCAT	 lpNICEVCAT;
	
	HINSTANCE hDll = LoadLibrary("NVCAT.dll");
	if(hDll == NULL) {
		AfxMessageBox("NVCAT.dll Loading Error");
		return;
	}
	
	lpNICEVCAT = (NICEVCAT)GetProcAddress(hDll, "NICEVCAT");
	if(lpNICEVCAT == NULL) {
		AfxMessageBox("NICEVCAT function Not found");
		return;
	}

	m_Senddata = sbuf;
	int ret = lpNICEVCAT(sbuf, rbuf);
	m_Recvdata = rbuf;
	
	CString cRet;
	cRet.Format(_T("리턴값 : %d"), ret);
	AfxMessageBox(cRet);
	
	if(ret != 1) {
		AfxMessageBox("요청 실패! 리턴값이 1이 아닙니다.");
		//return ;
	}
	
	UpdateData(FALSE);
}

void CNVCAT_TestDlg::OnButton23() 
{
	UpdateData(TRUE);	
	
	char FS = 0x1C;
	char sbuf[4096], rbuf[4096];
	memset(sbuf, 0x00, sizeof(sbuf));
	memset(rbuf, 0x00, sizeof(rbuf));
	
	sprintf(sbuf, "0300%c10%cL%c%s%c%s%c%s%c%s%c%c%c%s%c%c%c%s%c%c%c%c%cFiller%c%cPRO%c%c%c%c%c%c", FS, FS, FS, m_Money, FS, m_Tax, FS, m_Bongsa, FS, m_Halbu, FS, FS, FS, m_Catid, FS, FS, FS, m_Barcode, FS, FS, FS, FS, FS, FS, FS, FS, FS, FS, FS, FS, FS);
	
	typedef int (__stdcall *NICEVCATB)(char *send_data, char *recv_data);
	NICEVCATB	 lpNICEVCATB;
	
	HINSTANCE hDll = LoadLibrary("NVCAT.dll");
	if(hDll == NULL) {
		AfxMessageBox("NVCAT.dll Loading Error");
		return;
	}
	
	lpNICEVCATB = (NICEVCATB)GetProcAddress(hDll, "NICEVCATB");
	if(lpNICEVCATB == NULL) {
		AfxMessageBox("NICEVCATB function Not found");
		return;
	}

	m_Senddata = sbuf;

	AfxMessageBox("NICEVCATB API 사용합니다.");
	int ret = lpNICEVCATB(sbuf, rbuf);
	m_Recvdata = rbuf;
	
	CString cRet;
	cRet.Format(_T("리턴값 : %d"), ret);
	AfxMessageBox(cRet);
	
	if(ret != 1) {
		AfxMessageBox("요청 실패! 리턴값이 1이 아닙니다.");
		//return ;
	}
	
	UpdateData(FALSE);
}

void CNVCAT_TestDlg::OnButton24() 
{
	UpdateData(TRUE);	
	
	char FS = 0x1C;
	char sbuf[4096], rbuf[4096];
	memset(sbuf, 0x00, sizeof(sbuf));
	memset(rbuf, 0x00, sizeof(rbuf));
	
	char cHalbu[16];
	memset(cHalbu, 0x00, sizeof(cHalbu));
	sprintf(cHalbu, "%02d", atoi(m_Halbu));
	
	sprintf(sbuf, "0520%c30%cL%c%s%c%s%c%s%c%s%c%s%c%s%c%s%c%c%c%s%c%c%c%c%cFiller%c%cPRO%c%c%c%c%c%c", FS, FS, FS, m_Money, FS, m_Tax, FS, m_Bongsa, FS, m_Halbu, FS, m_ApprNo, FS, m_ApprDt, FS, m_Catid, FS, FS, FS, m_Barcode, FS, FS, FS, FS, FS, FS, FS, FS, FS, FS, FS, FS, FS);
	
	typedef int (__stdcall *NICEVCATB)(char *send_data, char *recv_data);
	NICEVCATB	 lpNICEVCATB;
	
	HINSTANCE hDll = LoadLibrary("NVCAT.dll");
	if(hDll == NULL) {
		AfxMessageBox("NVCAT.dll Loading Error");
		return;
	}
	
	lpNICEVCATB = (NICEVCATB)GetProcAddress(hDll, "NICEVCATB");
	if(lpNICEVCATB == NULL) {
		AfxMessageBox("NICEVCATB function Not found");
		return;
	}
	
	m_Senddata = sbuf;
	AfxMessageBox("NICEVCATB API 사용합니다.");
	int ret = lpNICEVCATB(sbuf, rbuf);
	m_Recvdata = rbuf;
	
	CString cRet;
	cRet.Format(_T("리턴값 : %d"), ret);
	AfxMessageBox(cRet);
	
	if(ret != 1) {
		AfxMessageBox("요청 실패! 리턴값이 1이 아닙니다.");
		//return ;
	}
	
	UpdateData(FALSE);
}

void CNVCAT_TestDlg::OnButton25() 
{
	UpdateData(TRUE);
	
	typedef int (__stdcall *CHK_CASHIC2)();
	CHK_CASHIC2	 lpCHK_CASHIC2;
	typedef int (__stdcall *REQ_SELECTBTN)(char *type, char *send_data, char *recv_data);
	REQ_SELECTBTN	 lpREQ_SELECTBTN;
	typedef int (__stdcall *NICEVCAT)(char *send_data, char *recv_data);
	NICEVCAT	 lpNICEVCAT;
	typedef int (__stdcall *REQ_CASHIC_AL)(char *cReaderType, char *cRecvData);
	REQ_CASHIC_AL	 lpREQ_CASHIC_AL;
	
	HINSTANCE hDll = LoadLibrary("NVCAT.dll");
	if(hDll == NULL) {
		AfxMessageBox("NVCAT.dll Loading Error");
		return;
	}
	
	lpCHK_CASHIC2 = (CHK_CASHIC2)GetProcAddress(hDll, "CHK_CASHIC2");
	if(lpCHK_CASHIC2 == NULL) {
		AfxMessageBox("CHK_CASHIC2 function Not found");
		return;
	}
	lpREQ_SELECTBTN = (REQ_SELECTBTN)GetProcAddress(hDll, "REQ_SELECTBTN");
	if(lpREQ_SELECTBTN == NULL) {
		AfxMessageBox("REQ_SELECTBTN function Not found");
		return;
	}
	lpNICEVCAT = (NICEVCAT)GetProcAddress(hDll, "NICEVCAT");
	if(lpNICEVCAT == NULL) {
		AfxMessageBox("NICEVCAT function Not found");
		return;
	}
	lpREQ_CASHIC_AL = (REQ_CASHIC_AL)GetProcAddress(hDll, "REQ_CASHIC_AL");
	if(lpREQ_CASHIC_AL == NULL) {
		AfxMessageBox("REQ_CASHIC_AL function Not found");
		return;
	}

	char FS = 0x1C;
	char sbuf[4096], rbuf[4096];
	memset(sbuf, 0x00, sizeof(sbuf));
	memset(rbuf, 0x00, sizeof(rbuf));
	int ret;
	
	AfxMessageBox("현금IC 가능한 카드 체크합니다.");
	ret = lpCHK_CASHIC2();
	
	memset(sbuf, 0x00, sizeof(sbuf));
	memset(rbuf, 0x00, sizeof(rbuf));
	if(ret >= 1) {
		AfxMessageBox("현금IC 가능한 카드입니다.");
		
		ret = lpREQ_SELECTBTN("2", "현금IC 거래를 하시겠습니까?", rbuf); //"1" : 서명패드, "2" 터치스크린으로 요청
		
		if(ret != 1) {
			AfxMessageBox("사용자 선택 버튼 표시 요청 실패!");
			return ;
		}

		if(memcmp(rbuf, "01", 2) == 0) {
			AfxMessageBox("현금IC 거래 선택을 했습니다. 현금IC 거래를 진행합니다.");

			ret = lpREQ_SELECTBTN("2", "체크카드만 현금IC 진행 하시겠습니까?", rbuf); //"1" : 서명패드, "2" 터치스크린으로 요청
			
			if(ret != 1) {
				AfxMessageBox("사용자 선택 버튼 표시 요청 실패!");
				return ;
			}
			
			if(memcmp(rbuf, "01", 2) == 0) {
				AfxMessageBox("체크카드만 현금IC 거래로 진행합니다.\n체크카드 여부 확인 합니다.");
				
				memset(rbuf, 0x00, sizeof(rbuf));
				ret = lpREQ_CASHIC_AL("1", rbuf); //"1" : 리더기, "2" : 서명패드
				
				if(ret >= 1) {
					if(strstr(rbuf, "DEBIT") != NULL || strstr(rbuf, "CHECK") != NULL)
					{
						AfxMessageBox("체크 카드입니다! 현금IC 거래를 진행합니다.");
						if(_ttoi(m_Money) >= 50001) {
							AfxMessageBox("현금IC 일반 거래로 진행합니다. - 거래금액 50001원 이상");
							sprintf(sbuf, "0200%cI1%c00%c%s%c%s%c%s%c%c%c%s%c%c%c%cFiller%c%c%c%c%c%c", FS, FS, FS, m_Bongsa, FS, m_Tax, FS, m_Money, FS, FS, FS, m_Catid, FS, FS, FS, FS, FS, FS, FS, FS, FS, FS);
						} else {
							AfxMessageBox("현금IC 간소화 거래로 진행합니다. - 거래금액 50001원 미만");
							sprintf(sbuf, "0200%cI1%c01%c%s%c%s%c%s%c%c%c%s%c%c%c%cFiller%c%c%c%c%c%c", FS, FS, FS, m_Bongsa, FS, m_Tax, FS, m_Money, FS, FS, FS, m_Catid, FS, FS, FS, FS, FS, FS, FS, FS, FS, FS);
						}
					} else {
						AfxMessageBox("체크 카드가 아닙니다! 신용 거래를 진행합니다.");
						sprintf(sbuf, "0200%c10%cC%c%s%c%s%c%s%c%s%c%c%c%s%c%c%c%c%c%c%c%cFiller%c", FS, FS, FS, m_Money, FS, m_Tax, FS, m_Bongsa, FS, m_Halbu, FS, FS, FS, m_Catid, FS, FS, FS, FS, FS, FS, FS, FS, FS);
					}
				} else {
					AfxMessageBox("체크 카드 여부 확인 실패! 신용 거래를 진행합니다.");
					sprintf(sbuf, "0200%c10%cC%c%s%c%s%c%s%c%s%c%c%c%s%c%c%c%c%c%c%c%cFiller%c", FS, FS, FS, m_Money, FS, m_Tax, FS, m_Bongsa, FS, m_Halbu, FS, FS, FS, m_Catid, FS, FS, FS, FS, FS, FS, FS, FS, FS);
				}
			}
			else {
				AfxMessageBox("체크/신용카드 무관하게 현금IC 거래로 진행합니다.");
				if(_ttoi(m_Money) >= 50001) {
					AfxMessageBox("현금IC 일반 거래로 진행합니다. - 거래금액 50001원 이상");
					sprintf(sbuf, "0200%cI1%c00%c%s%c%s%c%s%c%c%c%s%c%c%c%cFiller%c%c%c%c%c%c", FS, FS, FS, m_Bongsa, FS, m_Tax, FS, m_Money, FS, FS, FS, m_Catid, FS, FS, FS, FS, FS, FS, FS, FS, FS, FS);
				} else {
					AfxMessageBox("현금IC 간소화 거래로 진행합니다. - 거래금액 50001원 미만");
					sprintf(sbuf, "0200%cI1%c01%c%s%c%s%c%s%c%c%c%s%c%c%c%cFiller%c%c%c%c%c%c", FS, FS, FS, m_Bongsa, FS, m_Tax, FS, m_Money, FS, FS, FS, m_Catid, FS, FS, FS, FS, FS, FS, FS, FS, FS, FS);
				}
			}
		} else {
			AfxMessageBox("현금IC 거래 선택하지 않았습니다. 신용 거래를 진행합니다.");
			sprintf(sbuf, "0200%c10%cC%c%s%c%s%c%s%c%s%c%c%c%s%c%c%c%c%c%c%c%cFiller%c", FS, FS, FS, m_Money, FS, m_Tax, FS, m_Bongsa, FS, m_Halbu, FS, FS, FS, m_Catid, FS, FS, FS, FS, FS, FS, FS, FS, FS);
		}
	} else if(ret == 0) {
		AfxMessageBox("현금IC 카드 아님 (기타 체크카드). 신용 거래를 진행합니다.");
		sprintf(sbuf, "0200%c10%cC%c%s%c%s%c%s%c%s%c%c%c%s%c%c%c%c%c%c%c%cFiller%c", FS, FS, FS, m_Money, FS, m_Tax, FS, m_Bongsa, FS, m_Halbu, FS, FS, FS, m_Catid, FS, FS, FS, FS, FS, FS, FS, FS, FS);
	} else if(ret == -1) {
		AfxMessageBox("현금IC 카드 아님 (신용카드). 신용 거래를 진행합니다.");
		sprintf(sbuf, "0200%c10%cC%c%s%c%s%c%s%c%s%c%c%c%s%c%c%c%c%c%c%c%cFiller%c", FS, FS, FS, m_Money, FS, m_Tax, FS, m_Bongsa, FS, m_Halbu, FS, FS, FS, m_Catid, FS, FS, FS, FS, FS, FS, FS, FS, FS);
	} else {
		AfxMessageBox("현금IC 카드 여부 확인 실패! 신용 거래를 진행합니다.");
		sprintf(sbuf, "0200%c10%cC%c%s%c%s%c%s%c%s%c%c%c%s%c%c%c%c%c%c%c%cFiller%c", FS, FS, FS, m_Money, FS, m_Tax, FS, m_Bongsa, FS, m_Halbu, FS, FS, FS, m_Catid, FS, FS, FS, FS, FS, FS, FS, FS, FS);
	}
	
	memset(rbuf, 0x00, sizeof(rbuf));
	m_Senddata = sbuf;
	ret = lpNICEVCAT(sbuf, rbuf);
	m_Recvdata = rbuf;
	
	CString cRet;
	cRet.Format(_T("리턴값 : %d"), ret);
	AfxMessageBox(cRet);
	
	if(ret != 1) {
		AfxMessageBox("요청 실패! 리턴값이 1이 아닙니다.");
		//return ;
	}
	
	UpdateData(FALSE);	
}

void CNVCAT_TestDlg::OnButton26() 
{
	UpdateData(TRUE);	
	
	typedef int (__stdcall *REQ_BARCODE)(char *type, char *recv_data);
	REQ_BARCODE	 lpREQ_BARCODE;
	typedef int (__stdcall *NICEVCATB)(char *send_data, char *recv_data);
	NICEVCATB	 lpNICEVCATB;
	
	HINSTANCE hDll = LoadLibrary("NVCAT.dll");
	if(hDll == NULL) {
		AfxMessageBox("NVCAT.dll Loading Error");
		return;
	}
	
	lpREQ_BARCODE = (REQ_BARCODE)GetProcAddress(hDll, "REQ_BARCODE");
	if(lpREQ_BARCODE == NULL) {
		AfxMessageBox("REQ_BARCODE function Not found");
		return;
	}
	lpNICEVCATB = (NICEVCATB)GetProcAddress(hDll, "NICEVCATB");
	if(lpNICEVCATB == NULL) {
		AfxMessageBox("NICEVCATB function Not found");
		return;
	}

	char FS = 0x1C;
	char sbuf[4096], rbuf[4096];
	memset(sbuf, 0x00, sizeof(sbuf));
	memset(rbuf, 0x00, sizeof(rbuf));
	int ret;
	
	AfxMessageBox("바코드 리딩 요청합니다.\nNVCAT 환경설정에서 서명패드로 요청!");
	ret = lpREQ_BARCODE("1", rbuf); //TYPE : "0"(리더기), "1"(서명패드)
	
	CString cRet;
	cRet.Format(_T("리턴값 : %d"), ret);
	AfxMessageBox(cRet);
	
	if(ret != 1) {
		AfxMessageBox("바코드리딩 요청 실패! 리턴값이 1이 아닙니다.");
		return ;
	}
	
	m_Barcode = rbuf;
		
	AfxMessageBox("바코드리딩이 완료되었습니다.\n간편결제 통합 거래를 진행합니다!");
	
	memset(sbuf, 0x00, sizeof(sbuf));
	memset(rbuf, 0x00, sizeof(rbuf));
	sprintf(sbuf, "0300%c10%cL%c%s%c%s%c%s%c%s%c%c%c%s%c%c%c%s%c%c%c%c%cFiller%c%cPRO%c%c%c%c%c%c", FS, FS, FS, m_Money, FS, m_Tax, FS, m_Bongsa, FS, m_Halbu, FS, FS, FS, m_Catid, FS, FS, FS, m_Barcode, FS, FS, FS, FS, FS, FS, FS, FS, FS, FS, FS, FS, FS);
	
	m_Senddata = sbuf;
	ret = lpNICEVCATB(sbuf, rbuf);
	m_Recvdata = rbuf;
	
	cRet.Format(_T("리턴값 : %d"), ret);
	AfxMessageBox(cRet);
	
	if(ret != 1) {
		AfxMessageBox("요청 실패! 리턴값이 1이 아닙니다.");
		//return ;
	}
	
	UpdateData(FALSE);
}

void CNVCAT_TestDlg::OnButton27() 
{
	UpdateData(TRUE);
	
	typedef int (__stdcall *REQ_CASHIC_AL)(char *cReaderType, char *cRecvData);
	REQ_CASHIC_AL	 lpREQ_CASHIC_AL;
	
	HINSTANCE hDll = LoadLibrary("NVCAT.dll");
	if(hDll == NULL) {
		AfxMessageBox("NVCAT.dll Loading Error");
		return;
	}
	
	lpREQ_CASHIC_AL = (REQ_CASHIC_AL)GetProcAddress(hDll, "REQ_CASHIC_AL");
	if(lpREQ_CASHIC_AL == NULL) {
		AfxMessageBox("REQ_CASHIC_AL function Not found");
		return;
	}
	
	char cRecvData[1024];
	memset(cRecvData, 0x00, sizeof(cRecvData));

	int ret = lpREQ_CASHIC_AL("1", cRecvData);
	
	CString cRet;
	cRet.Format(_T("리턴값 : %d"), ret);
	AfxMessageBox(cRet);

	m_Recvdata = cRecvData;
	
	UpdateData(FALSE);	
}
