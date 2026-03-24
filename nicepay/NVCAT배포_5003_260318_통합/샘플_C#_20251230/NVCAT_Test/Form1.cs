using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Windows.Forms;
using System.Runtime.InteropServices;

namespace WindowsFormsApplication1
{
    public partial class Form1 : Form
    {
        [DllImport("NVCAT.dll", CharSet = CharSet.Unicode)]
        public static extern int NICEVCAT(byte[] SendBuf, byte[] RecvBuf);
        [DllImport("NVCAT.dll", CharSet = CharSet.Unicode)]
        public static extern int REQ_STOP();
        [DllImport("NVCAT.dll", CharSet = CharSet.Unicode)]
        public static extern int RESTART();
        [DllImport("NVCAT.dll", CharSet = CharSet.Unicode)]
        public static extern int READER_RESET(string time);
        [DllImport("NVCAT.dll", CharSet = CharSet.Unicode)]
        public static extern int GET_APPR(byte[] RecvBuf);
        [DllImport("NVCAT.dll", CharSet = CharSet.Unicode)]
        public static extern int CHK_CARDBIN(byte[] RecvBuf);
        [DllImport("NVCAT.dll", CharSet = CharSet.Unicode)]
        public static extern int CHK_CASHIC();
        [DllImport("NVCAT.dll", CharSet = CharSet.Unicode)]
        public static extern int CHK_CASHIC_MP();
        [DllImport("NVCAT.dll", CharSet = CharSet.Unicode)]
        public static extern int CHK_CARDIN_MP(byte[] RecvBuf);
        [DllImport("NVCAT.dll", CharSet = CharSet.Unicode)]
        public static extern int REQ_BARCODE(byte[] hwtype, byte[] RecvBuf);
        [DllImport("NVCAT.dll", CharSet = CharSet.Unicode)]
        public static extern int CHK_CASHIC2();
        [DllImport("NVCAT.dll", CharSet = CharSet.Unicode)]
        public static extern int NVCATSHUTDOWN();
        [DllImport("NVCAT.dll", CharSet = CharSet.Unicode)]
        public static extern int SetCnlDisableYN(byte[] NiceDownYN, byte[] CustomCnl);
        [DllImport("NVCAT.dll", CharSet = CharSet.Unicode)]
        public static extern int GetMac(byte[] Mac);
        [DllImport("NVCAT.dll", CharSet = CharSet.Unicode)]
        public static extern int REQ_TITLOCK();
        [DllImport("NVCAT.dll", CharSet = CharSet.Unicode)]
        public static extern int REQ_CASHIC_AL(byte[] bReaderType, byte[] bRecvBuf);
        [DllImport("NVCAT.dll", CharSet = CharSet.Unicode)]
        public static extern int GetDecSignData(int signtype, byte[] bDir, byte[] bOutdata);
        [DllImport("NVCAT.dll", CharSet = CharSet.Unicode)]
        public static extern int REQ_CMD(byte[] btype, byte[] bcmd, byte[] bSendBuf, byte[] bRecvBuf);

        public Form1()
        {
            InitializeComponent();
        }

        private void buttonReq_Click(object sender, EventArgs e) //승인요청
        {
            string FS = ((char)28).ToString();
            string Halbu = String.Format("{0:00}", comboHalbu.SelectedIndex);
            string SendData = "";

            switch (comboDeal.SelectedIndex)
            {
                case 0: //신용승인
                    SendData = "0200" + FS + "10" + FS + "C" + FS + textMoney.Text + FS + textTax.Text + FS + textBongsa.Text + FS + Halbu + FS + "" + FS + "" + FS + textCatid.Text + FS + FS + FS + FS + "" + FS + FS + FS + FS + "신용승인" + FS;
                    break;
                case 1: //FALLBACK
                    SendData = "0200" + FS + "10" + FS + "F" + FS + textMoney.Text + FS + textTax.Text + FS + textBongsa.Text + FS + Halbu + FS + "" + FS + "" + FS + textCatid.Text + FS + FS + FS + FS + "" + FS + FS + FS + FS + "신용승인FALLBACK" + FS;
                    break;
                case 2: //신용취소
                    SendData = "0420" + FS + "10" + FS + "C" + FS + textMoney.Text + FS + textTax.Text + FS + textBongsa.Text + FS + Halbu + FS + textAgreenum.Text + FS + textAgreedate.Text + FS + textCatid.Text + FS + FS + FS + FS + "" + FS + FS + FS + FS + "신용취소" + FS;
                    break;
                case 3: //현금승인
                    Halbu = String.Format("{0:00}", comboHalbu.SelectedIndex + 1);

                    if (radioButton1.Checked == true)
                    {
                        SendData = "0200" + FS + "21" + FS + "K" + FS + textMoney.Text + FS + textTax.Text + FS + textBongsa.Text + FS + Halbu + FS + "" + FS + "" + FS + textCatid.Text + FS + FS + FS + "" + FS + FS + FS + FS + FS + "현금영수증승인KEYIN방식" + FS;
                    }
                    else if (radioButton2.Checked == true)
                    {
                        SendData = "0200" + FS + "21" + FS + "P" + FS + textMoney.Text + FS + textTax.Text + FS + textBongsa.Text + FS + Halbu + FS + "" + FS + "" + FS + textCatid.Text + FS + FS + FS + textcashno.Text + FS + FS + FS + FS + FS + "현금영수증승인POS입력" + FS;
                    }
                    else if (radioButton3.Checked == true)
                    {
                        SendData = "0200" + FS + "21" + FS + "C" + FS + textMoney.Text + FS + textTax.Text + FS + textBongsa.Text + FS + Halbu + FS + "" + FS + "" + FS + textCatid.Text + FS + FS + FS + FS + FS + FS + FS + FS + "현금영수증승인CARD방식" + FS;
                    }
                    else 
                    {
                        SendData = "0200" + FS + "21" + FS + "T" + FS + textMoney.Text + FS + textTax.Text + FS + textBongsa.Text + FS + Halbu + FS + "" + FS + "" + FS + textCatid.Text + FS + FS + FS + FS + FS + FS + FS + FS + "현금영수증승인터치방식" + FS;
                    }
                    break;
                case 4: //현금취소
                    Halbu = String.Format("{0:00}", comboHalbu.SelectedIndex + 1);

                    if (radioButton1.Checked == true)
                    {
                        SendData = "0420" + FS + "21" + FS + "K" + FS + textMoney.Text + FS + textTax.Text + FS + textBongsa.Text + FS + Halbu + FS + textAgreenum.Text + FS + textAgreedate.Text + FS + textCatid.Text + FS + FS + FS + "" + FS + FS + FS + FS + FS + "현금영수증취소KEYIN방식" + FS;
                    }
                    else if (radioButton2.Checked == true)
                    {
                        SendData = "0420" + FS + "21" + FS + "P" + FS + textMoney.Text + FS + textTax.Text + FS + textBongsa.Text + FS + Halbu + FS + textAgreenum.Text + FS + textAgreedate.Text + FS + textCatid.Text + FS + FS + FS + textcashno.Text + FS + FS + FS + FS + FS + "현금영수증취소POS입력" + FS;
                    }
                    else if (radioButton3.Checked == true)
                    {
                        SendData = "0420" + FS + "21" + FS + "C" + FS + textMoney.Text + FS + textTax.Text + FS + textBongsa.Text + FS + Halbu + FS + textAgreenum.Text + FS + textAgreedate.Text + FS + textCatid.Text + FS + FS + FS + FS + FS + FS + FS + FS + "현금영수증취소CARD방식" + FS;
                    }
                    else
                    {
                        SendData = "0420" + FS + "21" + FS + "T" + FS + textMoney.Text + FS + textTax.Text + FS + textBongsa.Text + FS + Halbu + FS + textAgreenum.Text + FS + textAgreedate.Text + FS + textCatid.Text + FS + FS + FS + FS + FS + FS + FS + FS + "현금영수증취소터치방식" + FS;
	
                    }
                    break;
                case 5: //은련승인
                    SendData = "0200" + FS + "UP" + FS + "C" + FS + textMoney.Text + FS + textTax.Text + FS + textBongsa.Text + FS + Halbu + FS + "" + FS + "" + FS + textCatid.Text + FS + FS + FS + FS + FS + FS + FS + FS + "해외은련승인요청" + FS;
                    break;
                case 6: //은련취소
                    SendData = "0420" + FS + "UP" + FS + "C" + FS + textMoney.Text + FS + textTax.Text + FS + textBongsa.Text + FS + Halbu + FS + textAgreenum.Text + FS + textAgreedate.Text + FS + textCatid.Text + FS + FS + FS + FS + FS + FS + FS + FS + "해외은련취소요청" + FS;
                    break;
                case 7: //수표조회
                    string Billtpcd = comboBilltp.Text.Substring(0 ,2);
                    string Billmoneycd = comboBillmoney.Text.Substring(0, 2);
                    SendData = "0200" + FS + "20" + FS + "K" + FS + Billtpcd + FS + Billmoneycd + FS + Billno.Text + FS + Billdt.Text + FS + billsn.Text + FS + billamt.Text + FS + Billserial.Text + FS;
                    break;
                case 8: //현금IC승인
                    SendData = "0200" + FS + "I1" + FS + "00" + FS + textBongsa.Text + FS + textTax.Text + FS + textMoney.Text + FS + FS + FS + textCatid.Text + FS + FS + FS + FS + "현금IC승인" + FS;
                    break;
                case 9: //현금IC취소
                    SendData = "0420" + FS + "I4" + FS + "00" + FS + textBongsa.Text + FS + textTax.Text + FS + textMoney.Text + FS + textAgreenum.Text + FS + textAgreedate.Text + FS + textCatid.Text + FS + FS + FS + FS + "현금IC취소" + FS;
                    break;
                case 10: //현금IC잔액조회
                    SendData = "0200" + FS + "I3" + FS + "00" + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + "현금IC잔액조회" + FS;
                    break;
                case 11: //현금IC승인결과
                    SendData = "0200" + FS + "I2" + FS + "00" + FS + textBongsa.Text + FS + textTax.Text + FS + textMoney.Text + FS + textAgreenum.Text + FS + textAgreedate.Text + FS + textCatid.Text + FS + FS + FS + FS + "현금IC승인결과" + FS;
                    break;
                case 12: //현금IC취소결과
                    SendData = "0420" + FS + "I2" + FS + "00" + FS + textBongsa.Text + FS + textTax.Text + FS + textMoney.Text + FS + textAgreenum.Text + FS + textAgreedate.Text + FS + textCatid.Text + FS + FS + FS + FS + "현금IC취소결과" + FS;
                    break;
                case 13: //카드정보조회
                    SendData = "0300" + FS + "10" + FS + "I" + FS + "1" + FS + "0" + FS + "0" + FS + "00" + FS + "" + FS + "" + FS + FS + FS + FS + FS + "" + FS + FS + FS + FS + FS + FS + "CNS" + FS + "" + FS + "" + FS + "" + FS + "" + FS + FS + FS + FS + FS + FS;
                    break;
                case 14: //NICE HIPASS(등록:N1)
                    SendData = "0300" + FS + "N1" + FS + "L" + FS + textMoney.Text + FS + textTax.Text + FS + textBongsa.Text + FS + Halbu + FS + "" + FS + "" + FS + FS + FS + FS + FS + FS + FS + FS + FS + "Filler" + FS + "881130   00" + FS + FS + FS + FS + FS + "NVH2013055|이주용1" + FS + "" + FS + FS + FS + FS + FS;
                    break;
                case 15: //NICE HIPASS(승인:N2)
                    SendData = "0300" + FS + "N2" + FS + "L" + FS + textMoney.Text + FS + textTax.Text + FS + textBongsa.Text + FS + Halbu + FS + "" + FS + "" + FS + FS + FS + FS + textcashno.Text + FS + FS + FS + FS + FS + "Filler" + FS + "" + FS + FS + FS + FS + FS + "NVH2013055|이주용1" + FS + SignData.Text + FS + FS + FS + FS + FS;
                    break;
                case 16: //NICE HIPASS(취소:N2)
                    SendData = "0520" + FS + "N2" + FS + "L" + FS + textMoney.Text + FS + textTax.Text + FS + textBongsa.Text + FS + Halbu + FS + textAgreenum.Text + FS + textAgreedate.Text + FS + FS + FS + FS + textcashno.Text + FS + FS + FS + FS + FS + "Filler" + FS + "" + FS + FS + FS + FS + FS + "NVH2013055|이주용1" + FS + SignData.Text + FS + FS + FS + FS + FS;
                    break;
                case 17: //NICE HIPASS(삭제:N3)
                    SendData = "0300" + FS + "N3" + FS + "L" + FS + textMoney.Text + FS + textTax.Text + FS + textBongsa.Text + FS + Halbu + FS + "" + FS + "" + FS + FS + FS + FS + textcashno.Text + FS + FS + FS + FS + FS + "Filler" + FS + "" + FS + FS + FS + FS + FS + "NVH2013055|이주용1" + FS + FS + FS + FS + FS + FS;
                    break;
                case 18: //그린카드적립승인
                    SendData = "0320" + FS + "48" + FS + "I" + FS + textMoney.Text + FS + textTax.Text + FS + textBongsa.Text + FS + FS + "" + FS + "" + FS + textCatid.Text + FS + FS + FS + FS + FS + FS + FS + FS + "" + FS + FS + "HPS" + FS + "" + FS + textcashno.Text + FS + FS + FS + FS + FS + FS + FS;
                    break;
                case 19: //그린카드적립취소
                    SendData = "0540" + FS + "48" + FS + "I" + FS + textMoney.Text + FS + textTax.Text + FS + textBongsa.Text + FS + FS + textAgreenum.Text + FS + textAgreedate.Text + FS + textCatid.Text + FS + FS + FS + FS + FS + FS + FS + FS + "" + FS + FS + "HPS" + FS + "" + FS + textcashno.Text + FS + FS + FS + FS + FS + FS + FS;
                    break;
                case 20: //DCC환율조회(POS 2TR)
                    SendData = "0200" + FS + "D1" + FS + "C" + FS + textMoney.Text + FS + textTax.Text + FS + textBongsa.Text + FS + Halbu + FS + FS + FS + textCatid.Text + FS + "410" + FS + textMoney.Text + FS + "0" + FS + FS + textcashno.Text + FS + FS + FS + FS + "" + FS + SignData.Text + FS + FS + FS + FS + FS;
                    break;
                case 21: //DCC원화통화승인(POS 2TR)
                    SendData = "0200" + FS + "D2" + FS + "C" + FS + textMoney.Text + FS + textTax.Text + FS + textBongsa.Text + FS + Halbu + FS + FS + FS + textCatid.Text + FS + "410" + FS + textMoney.Text + FS + "0" + FS + FS + textcashno.Text + FS + FS + FS + FS + "" + FS + SignData.Text + FS + FS + FS + FS + FS;
                    break;
                case 22: //DCC자국통화승인(POS 2TR)
                    SendData = "0200" + FS + "D3" + FS + "C" + FS + textMoney.Text + FS + textTax.Text + FS + textBongsa.Text + FS + Halbu + FS + FS + FS + textCatid.Text + FS + "410" + FS + textMoney.Text + FS + "0" + FS + FS + textcashno.Text + FS + FS + FS + FS + "" + FS + SignData.Text + FS + FS + FS + FS + FS;
                    break;
                case 23: //무카드신용부분취소 (LJY20220224)
                    MessageBox.Show("취소할 금액/원거래 승인번호/원거래 승인날짜/거래일련번호/원거래 금액/전문TEXT PCL 전문 구성 필요");
                    SendData = "0520" + FS + "30" + FS + "N" + FS + textMoney.Text + FS + textTax.Text + FS + textBongsa.Text + FS + Halbu + FS + textAgreenum.Text + FS + textAgreedate.Text + FS + textCatid.Text + FS + FS + FS + textcashno.Text + FS + FS + FS + FS + FS + "" + FS + "P000000001004" + FS + "PCL" + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS;
                    break;
                case 24: //컵보증금 (LSY20220518)
                    //컵보증금은 원거래고유번호필드에 넣습니다(CD+10자리)
                    SendData = "0200" + FS + "10" + FS + "C" + FS + textMoney.Text + FS + textTax.Text + FS + textBongsa.Text + FS + Halbu + FS + "" + FS + "" + FS + textCatid.Text + FS + FS + FS + FS + "" + FS + FS + FS + FS + "신용승인" + FS + FS + SignData.Text + FS + FS + FS + FS + FS + FS + FS + textUniNum.Text + FS + FS + FS;
                    break;
                case 25: //행안부모바일운전면허 (LJY20251230)
                    SendData = "0200" + FS + "HM" + FS + textBox_HM_Num.Text + FS + textBox_HM_Qr.Text + FS + textBox_HM_Filler1.Text + FS + textBox_HM_Filler2.Text + FS;
                    break;
            }

            byte[] mSend = System.Text.Encoding.GetEncoding(1252).GetBytes(SendData);
            byte[] mRecv = new byte[2048];

            int ret = NICEVCAT(mSend, mRecv);
            MessageBox.Show(ret.ToString()); //리턴값 처리 꼭 해주세요.

            if (ret != 1)
            {
                //Application.Exit();
                return;
            }
            textRecvData.Text = System.Text.Encoding.Default.GetString(mRecv);

            if (comboDeal.SelectedIndex == 7)
            {
                //Application.Exit();
                return;
            }


            //================================================================================================================================================


            int i = 0, j = 0, k = 0;
            string recvdata = (textRecvData.Text).ToString();

            if (comboDeal.SelectedIndex == 25)
            {
                while (true)
                {
                    if (recvdata.Substring(i, 1) == FS)
                    {
                        j = j + 1;

                        switch (j)
                        {
                            case 1:
                                textBox1.Text = recvdata.Substring(k, i - k);
                                break;
                            case 2:
                                textBox2.Text = recvdata.Substring(k, i - k);
                                break;
                            case 3:
                                textBox3.Text = recvdata.Substring(k, i - k);
                                break;
                            case 4:
                                textBox_HM_Recv_Qr.Text = recvdata.Substring(k, i - k);
                                break;
                            case 5:
                                textBox_HM_Recv_Taxcode.Text = recvdata.Substring(k, i - k);
                                break;
                            case 6:
                                textBox_HM_Recv_Resultcode.Text = recvdata.Substring(k, i - k);
                                break;
                            case 7:
                                textBox_HM_Recv_Msg.Text = recvdata.Substring(k, i - k);
                                break;
                            case 8:
                                textBox_HM_Recv_Filler1.Text = recvdata.Substring(k, i - k);
                                break;
                            case 9:
                                textBox_HM_Recv_Filler2.Text = recvdata.Substring(k, i - k);
                                break;
                        }
                        k = i + 1;

                        if (j == 9)
                            break;
                    }
                    i = i + 1;
                }
            }
            else if (comboDeal.SelectedIndex == 8 || comboDeal.SelectedIndex == 9 || comboDeal.SelectedIndex == 10 || comboDeal.SelectedIndex == 11 || comboDeal.SelectedIndex == 12)
            {
                while (true)
                {
                    if (recvdata.Substring(i, 1) == FS)
                    {
                        j = j + 1;

                        switch (j)
                        {
                            case 1:
                                textBox1.Text = recvdata.Substring(k, i - k);
                                break;
                            case 2:
                                textBox2.Text = recvdata.Substring(k, i - k);
                                break;
                            case 3:
                                textBox3.Text = recvdata.Substring(k, i - k);
                                break;
                            case 4:
                                textBox4.Text = recvdata.Substring(k, i - k);
                                break;
                            case 5:
                                textBox5.Text = recvdata.Substring(k, i - k);
                                break;
                            case 6:
                                textBox6.Text = recvdata.Substring(k, i - k);
                                break;
                            case 7:
                                textBox14.Text = recvdata.Substring(k, i - k);
                                break;
                            case 8:
                                textBox9.Text = recvdata.Substring(k, i - k);
                                break;
                            case 9:
                                textBox8.Text = recvdata.Substring(k, i - k);
                                textAgreenum.Text = textBox8.Text;
                                break;
                            case 10:
                                textBox001.Text = recvdata.Substring(k, i - k);
                                break;
                            case 11:
                                textBox002.Text = recvdata.Substring(k, i - k);
                                break;
                            case 12:
                                textBox003.Text = recvdata.Substring(k, i - k);
                                break;
                            case 13:
                                textBox004.Text = recvdata.Substring(k, i - k);
                                break;
                            case 14:
                                textBox005.Text = recvdata.Substring(k, i - k);
                                break;
                            case 15:
                                textBox006.Text = recvdata.Substring(k, i - k);
                                break;
                            case 16:
                                textBox007.Text = recvdata.Substring(k, i - k);
                                break;
                            case 17:
                                textBox008.Text = recvdata.Substring(k, i - k);
                                break;
                            case 18:
                                textBox009.Text = recvdata.Substring(k, i - k);
                                break;
                            case 19:
                                textBox010.Text = recvdata.Substring(k, i - k);
                                break;
                            case 20:
                                textBox011.Text = recvdata.Substring(k, i - k);
                                break;
                            case 21:
                                textBox012.Text = recvdata.Substring(k, i - k);
                                break;
                            case 22:
                                textBox013.Text = recvdata.Substring(k, i - k);
                                break;
                            case 23:
                                textBox014.Text = recvdata.Substring(k, i - k);
                                break;
                            case 24:
                                textBox015.Text = recvdata.Substring(k, i - k);
                                break;
                        }
                        k = i + 1;

                        if (j == 24)
                            break;
                    }
                    i = i + 1;
                }
            }
            else if (comboDeal.SelectedIndex == 14 || comboDeal.SelectedIndex == 15 || comboDeal.SelectedIndex == 16 || comboDeal.SelectedIndex == 17)
            {
                while (true)
                {
                    if (recvdata.Substring(i, 1) == FS)
                    {
                        j = j + 1;

                        switch (j)
                        {
                            case 1:
                                textBox1.Text = recvdata.Substring(k, i - k);
                                break;
                            case 2:
                                textBox2.Text = recvdata.Substring(k, i - k);
                                break;
                            case 3:
                                textBox3.Text = recvdata.Substring(k, i - k);
                                break;
                            case 4:
                                textBox6.Text = recvdata.Substring(k, i - k);
                                break;
                            case 5:
                                textBox5.Text = recvdata.Substring(k, i - k);
                                break;
                            case 6:
                                textBox4.Text = recvdata.Substring(k, i - k);
                                break;
                            case 7:
                                textBox7.Text = recvdata.Substring(k, i - k);
                                break;
                            case 8:
                                textBox8.Text = recvdata.Substring(k, i - k);
                                textAgreenum.Text = textBox8.Text;
                                break;
                            case 9:
                                textBox9.Text = recvdata.Substring(k, i - k);
                                break;
                            case 10:
                                textBox10.Text = recvdata.Substring(k, i - k);
                                break;
                            case 11:
                                textBox11.Text = recvdata.Substring(k, i - k);
                                break;
                            case 12:
                                textBox12.Text = recvdata.Substring(k, i - k);
                                break;
                            case 13:
                                textBox13.Text = recvdata.Substring(k, i - k);
                                break;
                            case 14:
                                textBox14.Text = recvdata.Substring(k, i - k);
                                break;
                            case 15:
                                textBox15.Text = recvdata.Substring(k, i - k);
                                break;
                            case 16:
                                textBox16.Text = recvdata.Substring(k, i - k);
                                break;
                            case 17:
                                textBox17.Text = recvdata.Substring(k, i - k);
                                break;
                            case 18:
                                textBox18.Text = recvdata.Substring(k, i - k);
                                break;
                            case 19:
                                textBox19.Text = recvdata.Substring(k, i - k);
                                break;
                            case 20:
                                textBox20.Text = recvdata.Substring(k, i - k);
                                break;
                            case 21:
                                textBox21.Text = recvdata.Substring(k, i - k);
                                break;
                            case 27:
                                textBox22.Text = recvdata.Substring(k, i - k);
                                break;
                        }
                        k = i + 1;

                        if (j == 27)
                            break;
                    }
                    i = i + 1;
                }
            }
            else
            {
                while (true)
                {
                    if (recvdata.Substring(i, 1) == FS)
                    {
                        j = j + 1;

                        switch (j)
                        {
                            case 1:
                                textBox1.Text = recvdata.Substring(k, i - k);
                                break;
                            case 2:
                                textBox2.Text = recvdata.Substring(k, i - k);
                                break;
                            case 3:
                                textBox3.Text = recvdata.Substring(k, i - k);
                                break;
                            case 4:
                                textBox6.Text = recvdata.Substring(k, i - k);
                                break;
                            case 5:
                                textBox5.Text = recvdata.Substring(k, i - k);
                                break;
                            case 6:
                                textBox4.Text = recvdata.Substring(k, i - k);
                                break;
                            case 7:
                                textBox7.Text = recvdata.Substring(k, i - k);
                                break;
                            case 8:
                                textBox8.Text = recvdata.Substring(k, i - k);
                                textAgreenum.Text = textBox8.Text;
                                break;
                            case 9:
                                textBox9.Text = recvdata.Substring(k, i - k);
                                break;
                            case 10:
                                textBox10.Text = recvdata.Substring(k, i - k);
                                break;
                            case 11:
                                textBox11.Text = recvdata.Substring(k, i - k);
                                break;
                            case 12:
                                textBox12.Text = recvdata.Substring(k, i - k);
                                break;
                            case 13:
                                textBox13.Text = recvdata.Substring(k, i - k);
                                break;
                            case 14:
                                textBox14.Text = recvdata.Substring(k, i - k);
                                break;
                            case 15:
                                textBox15.Text = recvdata.Substring(k, i - k);
                                break;
                            case 16:
                                textBox16.Text = recvdata.Substring(k, i - k);
                                break;
                            case 17:
                                textBox17.Text = recvdata.Substring(k, i - k);
                                break;
                            case 18:
                                textBox18.Text = recvdata.Substring(k, i - k);
                                break;
                            case 19:
                                textBox19.Text = recvdata.Substring(k, i - k);
                                break;
                            case 20:
                                textBox20.Text = recvdata.Substring(k, i - k);
                                break;
                            case 21:
                                textBox21.Text = recvdata.Substring(k, i - k);
                                break;
                        }
                        k = i + 1;

                        if (j == 21)
                            break;
                    }
                    i = i + 1;
                }
            }
        }

        private void buttonCnl_Click(object sender, EventArgs e) //취소
        {
            int ret = REQ_STOP();
        }

        private void Form1_Load(object sender, EventArgs e)
        {
            comboDeal.Items.Add("신용승인");
            comboDeal.Items.Add("FALLBACK");
            comboDeal.Items.Add("신용취소");
            comboDeal.Items.Add("현금승인");
            comboDeal.Items.Add("현금취소");
            comboDeal.Items.Add("은련승인");
            comboDeal.Items.Add("은련취소");
            comboDeal.Items.Add("수표조회");
            comboDeal.Items.Add("현금IC승인");
            comboDeal.Items.Add("현금IC취소");
            comboDeal.Items.Add("현금IC잔액조회");
            comboDeal.Items.Add("현금IC승인결과");
            comboDeal.Items.Add("현금IC취소결과");
            comboDeal.Items.Add("카드정보조회");
            comboDeal.Items.Add("NICE HIPASS(등록:N1)");
            comboDeal.Items.Add("NICE HIPASS(승인:N2)");
            comboDeal.Items.Add("NICE HIPASS(취소:N2)");
            comboDeal.Items.Add("NICE HIPASS(삭제:N3)");
            comboDeal.Items.Add("그린카드적립승인");
            comboDeal.Items.Add("그린카드적립취소");
            comboDeal.Items.Add("DCC환율조회(POS 2TR)");
            comboDeal.Items.Add("DCC원화통화승인(POS 2TR)");
            comboDeal.Items.Add("DCC자국통화승인(POS 2TR)");
            comboDeal.Items.Add("무카드신용부분취소"); //LJY20220224
            comboDeal.Items.Add("컵보증금"); //LSY20220518
            comboDeal.Items.Add("(행안부)모바일운전면허증"); //LJY20251230

            comboDeal.SelectedIndex = 0;

            comboBilltp.Items.Add("00 자기앞수표");
            comboBilltp.Items.Add("01 가계수표");
            comboBilltp.Items.Add("02 당좌수표");
            comboBilltp.SelectedIndex = 0;

            comboBillmoney.Items.Add("13 10만원");
            comboBillmoney.Items.Add("14 30만원");
            comboBillmoney.Items.Add("15 50만원");
            comboBillmoney.Items.Add("16 100만원");
            comboBillmoney.Items.Add("19 비정액");
            comboBillmoney.SelectedIndex = 0;

            textAgreedate.Text = DateTime.Now.ToString("yyMMdd");
        }

        private void comboDeal_SelectedIndexChanged(object sender, EventArgs e)
        {
            switch (comboDeal.SelectedIndex)
            {
                case 0:
                case 1:
                case 3:
                case 5:
                case 18:    
                    textAgreenum.Enabled = false;
                    textAgreenum.BackColor = Color.Gray;
                    textAgreedate.Enabled = false;
                    textAgreedate.BackColor = Color.Gray;
                    break;
                case 2:
                case 4:
                case 6:
                case 19:
                case 23: //LJY20220224
                    textAgreenum.Enabled = true;
                    textAgreenum.BackColor = Color.White;
                    textAgreedate.Enabled = true;
                    textAgreedate.BackColor = Color.White;
                    break;
                case 24:
                    textUniNum.Text = "CD0000000300";
                    break;
            }

            switch (comboDeal.SelectedIndex)
            {
                case 0:
                case 1:
                case 2:
                case 5:
                case 6:
                case 18:
                case 19:
                    label5.Text = "할부";
                    comboHalbu.Items.Clear();
                    comboHalbu.Items.Add("0개월");
                    comboHalbu.Items.Add("1개월");
                    comboHalbu.Items.Add("2개월");
                    comboHalbu.Items.Add("3개월");
                    comboHalbu.Items.Add("4개월");
                    comboHalbu.Items.Add("5개월");
                    comboHalbu.Items.Add("6개월");
                    comboHalbu.Items.Add("7개월");
                    comboHalbu.Items.Add("8개월");
                    comboHalbu.Items.Add("9개월");
                    comboHalbu.Items.Add("10개월");
                    comboHalbu.Items.Add("11개월");
                    comboHalbu.Items.Add("12개월");
                    comboHalbu.SelectedIndex = 0;
                    break;
                case 3:
                case 4:
                    label5.Text = "발급구분";
                    comboHalbu.Items.Clear();
                    comboHalbu.Items.Add("1소비자");
                    comboHalbu.Items.Add("2사업자");
                    comboHalbu.Items.Add("3자진발급");
                    comboHalbu.SelectedIndex = 0;
                    break;
                

            }
        }

        private void buttonRestart_Click(object sender, EventArgs e)
        {
            int ret = RESTART();
        }

        private void buttonReset_Click(object sender, EventArgs e)
        {
            int ret = READER_RESET(textBoxWaitTime.Text.ToString());
        }

        private void buttonNICEVCAT_Click(object sender, EventArgs e)
        {
            string FS = ((char)28).ToString();

            byte[] mSend = System.Text.Encoding.GetEncoding(1252).GetBytes(textBoxSend.Text);
            byte[] mRecv = new byte[2048];

            int ret = NICEVCAT(mSend, mRecv);
            MessageBox.Show(ret.ToString()); //리턴값 처리 꼭 해주세요.

            if (ret != 1)
                Application.Exit();

            textBoxRecv.Text = System.Text.Encoding.Default.GetString(mRecv);
        }

        private void button1_Click(object sender, EventArgs e)
        {
            byte[] mRecv = new byte[2048];
            int ret = CHK_CARDBIN(mRecv);

            if (ret == 1)
                MessageBox.Show(System.Text.Encoding.Default.GetString(mRecv));
        }

        private void button2_Click(object sender, EventArgs e)
        {
            int ret = CHK_CASHIC();
            MessageBox.Show(ret.ToString());
        }

        private void button3_Click(object sender, EventArgs e)
        {
            byte[] mRecv = new byte[2048];
            int ret = GET_APPR(mRecv);

            if (ret == 1)
                MessageBox.Show(System.Text.Encoding.Default.GetString(mRecv));
        }

        private void textBox004_TextChanged(object sender, EventArgs e)
        {

        }

        private void button4_Click(object sender, EventArgs e)
        {
            int ret = CHK_CASHIC_MP();
            MessageBox.Show(ret.ToString());
        }

        private void button5_Click(object sender, EventArgs e)
        {
            byte[] mRecv = new byte[2048];
            int ret = CHK_CARDIN_MP(mRecv);

            if (ret == 1)
                MessageBox.Show("응답데이터 : " + System.Text.Encoding.Default.GetString(mRecv));
            else
                MessageBox.Show("리턴값 확인하세요");
        }

        private void button6_Click(object sender, EventArgs e)
        {
            byte[] mSend = System.Text.Encoding.GetEncoding(1252).GetBytes("1");
            byte[] mRecv = new byte[2048];
            int ret = REQ_BARCODE(mSend, mRecv);

            if (ret == 1)
                MessageBox.Show("응답데이터 : " + System.Text.Encoding.Default.GetString(mRecv));
            else
                MessageBox.Show("리턴값 확인하세요 : " + ret);
        }

        private void button7_Click(object sender, EventArgs e)
        {
            int ret = CHK_CASHIC2();
            MessageBox.Show(ret.ToString());
        }

        private void button8_Click(object sender, EventArgs e)
        {
            int ret = NVCATSHUTDOWN();
        }

        private void button9_Click(object sender, EventArgs e)
        {
            MessageBox.Show("가맹점다운로드 테스트시 T / 운영시 1(Default)");
            MessageBox.Show("부정취소 미사용시 Y / 사용시 N(Default)");

            byte[] mNiceDownYN = System.Text.Encoding.GetEncoding(1252).GetBytes(NiceDownYN.Text);
            byte[] mCustomCnl = System.Text.Encoding.GetEncoding(1252).GetBytes(CustomCnl.Text);
            int ret = SetCnlDisableYN(mNiceDownYN, mCustomCnl);

            MessageBox.Show(ret.ToString()); //리턴값 처리 꼭 해주세요.
        }

        private void button10_Click(object sender, EventArgs e)
        {
            byte[] Mac = new byte[2048];
            int ret = GetMac(Mac);

            if (ret == 1)
                MessageBox.Show("MAC : " + System.Text.Encoding.Default.GetString(Mac));
            else
                MessageBox.Show("리턴값 확인하세요");
        }

        private void button11_Click(object sender, EventArgs e)
        {
            int ret = REQ_TITLOCK();
            MessageBox.Show(ret.ToString());
        }

        private void groupBox2_Enter(object sender, EventArgs e)
        {

        }

        private void button12_Click(object sender, EventArgs e)
        {
            byte[] bReaderType = System.Text.Encoding.GetEncoding(1252).GetBytes("1");
            byte[] bRecvBuf = new byte[2048];
            int ret = REQ_CASHIC_AL(bReaderType, bRecvBuf);

            MessageBox.Show("리턴값 : " + ret.ToString());
            MessageBox.Show("응답데이터 : " + System.Text.Encoding.Default.GetString(bRecvBuf));
        }

        private void button13_Click(object sender, EventArgs e)
        {
            byte[] bDir = System.Text.Encoding.GetEncoding(1252).GetBytes("C:\\NICEVCAT\\TouchSignBmp.bmp");
            byte[] bRecvBuf = new byte[2048];
            
            int ret = GetDecSignData(2, bDir, bRecvBuf);

            if (ret == 1)
                MessageBox.Show("응답데이터 : " + System.Text.Encoding.Default.GetString(bRecvBuf));
            else
                MessageBox.Show("서명데이터 변환 실패");
        }

        
        private void button14_Click(object sender, EventArgs e)
        {

            byte[] bReaderType = System.Text.Encoding.GetEncoding(1252).GetBytes("2");
            byte[] bCMD = System.Text.Encoding.GetEncoding(1252).GetBytes("68");
            byte[] bSendBuf = System.Text.Encoding.GetEncoding(1252).GetBytes("                1234567890123456");       
            byte[] bRecvBuf = new byte[2048];


            int ret = REQ_CMD(bReaderType, bCMD, bSendBuf, bRecvBuf);

            MessageBox.Show("리턴값 : " + ret.ToString());
            //MessageBox.Show("응답데이터 : " + System.Text.Encoding.Default.GetString(bRecvBuf));
        }

    }
}
