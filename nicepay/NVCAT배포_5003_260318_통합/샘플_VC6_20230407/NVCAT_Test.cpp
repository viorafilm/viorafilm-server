// NVCAT_Test.cpp : Defines the class behaviors for the application.
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
// CNVCAT_TestApp

BEGIN_MESSAGE_MAP(CNVCAT_TestApp, CWinApp)
	//{{AFX_MSG_MAP(CNVCAT_TestApp)
	//}}AFX_MSG
	ON_COMMAND(ID_HELP, CWinApp::OnHelp)
END_MESSAGE_MAP()

/////////////////////////////////////////////////////////////////////////////
// CNVCAT_TestApp construction

CNVCAT_TestApp::CNVCAT_TestApp()
{
}

/////////////////////////////////////////////////////////////////////////////
// The one and only CNVCAT_TestApp object

CNVCAT_TestApp theApp;

/////////////////////////////////////////////////////////////////////////////
// CNVCAT_TestApp initialization

BOOL CNVCAT_TestApp::InitInstance()
{
	// Standard initialization

	CNVCAT_TestDlg dlg;
	m_pMainWnd = &dlg;
	int nResponse = dlg.DoModal();
	if (nResponse == IDOK)
	{
	}
	else if (nResponse == IDCANCEL)
	{
	}

	// Since the dialog has been closed, return FALSE so that we exit the
	//  application, rather than start the application's message pump.
	return FALSE;
}
