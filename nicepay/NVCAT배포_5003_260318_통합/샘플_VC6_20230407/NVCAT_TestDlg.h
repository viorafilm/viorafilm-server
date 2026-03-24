// NVCAT_TestDlg.h : header file
//

#if !defined(AFX_NVCAT_TESTDLG_H__DC609CB4_0057_4BD3_A965_D65B924FF0A3__INCLUDED_)
#define AFX_NVCAT_TESTDLG_H__DC609CB4_0057_4BD3_A965_D65B924FF0A3__INCLUDED_

#if _MSC_VER > 1000
#pragma once
#endif // _MSC_VER > 1000

/////////////////////////////////////////////////////////////////////////////
// CNVCAT_TestDlg dialog

class CNVCAT_TestDlg : public CDialog
{
// Construction
public:
	CNVCAT_TestDlg(CWnd* pParent = NULL);	// standard constructor

// Dialog Data
	//{{AFX_DATA(CNVCAT_TestDlg)
	enum { IDD = IDD_NVCAT_TEST_DIALOG };
	CComboBox	m_cbCheckAmt;
	CComboBox	m_cbCheckTp;
	CComboBox	m_DealTp;
	CString	m_time;
	CString	m_Recvdata;
	CString	m_DeviceType;
	CString	m_ServerIp;
	CString	m_ServerPort;
	CString	m_CnlTestYn;
	CString	m_CnlUseYn;
	CString	m_FwFileDir;
	CString	m_ReaderType;
	CString	m_Halbu;
	CString	m_Money;
	CString	m_Tax;
	CString	m_Bongsa;
	CString	m_Catid;
	CString	m_ApprNo;
	CString	m_ApprDt;
	BOOL	m_CashKeyin;
	BOOL	m_CashTouch;
	BOOL	m_CashCard;
	CString	m_Barcode;
	CString	m_CheckTp;
	CString	m_CheckAmt;
	CString	m_CheckDealNo;
	CString	m_CheckDt;
	CString	m_CheckMoney;
	CString	m_CheckNo;
	CString	m_CheckPersonNo;
	CString	m_Txt;
	CString	m_Senddata;
	CString	m_DealType;
	CString	m_DeviceTp;
	CString	m_DealNo;
	CString	m_Domain;
	CString	m_IpAddress;
	//}}AFX_DATA

	// ClassWizard generated virtual function overrides
	//{{AFX_VIRTUAL(CNVCAT_TestDlg)
	protected:
	virtual void DoDataExchange(CDataExchange* pDX);	// DDX/DDV support
	//}}AFX_VIRTUAL

// Implementation
protected:
	HICON m_hIcon;

	// Generated message map functions
	//{{AFX_MSG(CNVCAT_TestDlg)
	virtual BOOL OnInitDialog();
	afx_msg void OnPaint();
	afx_msg HCURSOR OnQueryDragIcon();
	afx_msg void OnButton1();
	afx_msg void OnButton2();
	afx_msg void OnButton3();
	afx_msg void OnButton4();
	afx_msg void OnButton5();
	afx_msg void OnButton6();
	afx_msg void OnButton7();
	afx_msg void OnButton8();
	afx_msg void OnButton9();
	afx_msg void OnButton10();
	afx_msg void OnButton11();
	afx_msg void OnButton12();
	afx_msg void OnButton13();
	afx_msg void OnButton14();
	afx_msg void OnButton15();
	afx_msg void OnButton16();
	afx_msg void OnButton17();
	afx_msg void OnButton18();
	afx_msg void OnButton19();
	afx_msg void OnButton20();
	afx_msg void OnButton21();
	afx_msg void OnButton22();
	afx_msg void OnButton23();
	afx_msg void OnButton24();
	afx_msg void OnButton25();
	afx_msg void OnButton26();
	afx_msg void OnButton27();
	//}}AFX_MSG
	DECLARE_MESSAGE_MAP()
};

//{{AFX_INSERT_LOCATION}}
// Microsoft Visual C++ will insert additional declarations immediately before the previous line.

#endif // !defined(AFX_NVCAT_TESTDLG_H__DC609CB4_0057_4BD3_A965_D65B924FF0A3__INCLUDED_)
