// NVCAT_Test.h : main header file for the NVCAT_TEST application
//

#if !defined(AFX_NVCAT_TEST_H__B8479E78_875C_4196_B35D_D49DEE183E4D__INCLUDED_)
#define AFX_NVCAT_TEST_H__B8479E78_875C_4196_B35D_D49DEE183E4D__INCLUDED_

#if _MSC_VER > 1000
#pragma once
#endif // _MSC_VER > 1000

#ifndef __AFXWIN_H__
	#error include 'stdafx.h' before including this file for PCH
#endif

#include "resource.h"		// main symbols

/////////////////////////////////////////////////////////////////////////////
// CNVCAT_TestApp:
// See NVCAT_Test.cpp for the implementation of this class
//

class CNVCAT_TestApp : public CWinApp
{
public:
	CNVCAT_TestApp();

// Overrides
	// ClassWizard generated virtual function overrides
	//{{AFX_VIRTUAL(CNVCAT_TestApp)
	public:
	virtual BOOL InitInstance();
	//}}AFX_VIRTUAL

// Implementation

	//{{AFX_MSG(CNVCAT_TestApp)
	//}}AFX_MSG
	DECLARE_MESSAGE_MAP()
};


/////////////////////////////////////////////////////////////////////////////

//{{AFX_INSERT_LOCATION}}
// Microsoft Visual C++ will insert additional declarations immediately before the previous line.

#endif // !defined(AFX_NVCAT_TEST_H__B8479E78_875C_4196_B35D_D49DEE183E4D__INCLUDED_)
