using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Windows.Forms;
using System.Runtime.InteropServices;

namespace NVCAT_PayPro
{
    public partial class Form1 : Form
    {
        [DllImport("NVCAT.dll", CharSet = CharSet.Unicode)]
        public static extern int NICEVCATB(byte[] SendBuf, byte[] RecvBuf);
        [DllImport("NVCAT.dll", CharSet = CharSet.Unicode)]
        public static extern int REQ_STOP();
        [DllImport("NVCAT.dll", CharSet = CharSet.Unicode)]
        public static extern int Set_SvrInfo(byte[] Ip, byte[] Port);

        public Form1()
        {
            InitializeComponent();
        }

        private void buttonNICEVCAT_Click(object sender, EventArgs e)
        {
            string FS = ((char)28).ToString();

            byte[] mSend = System.Text.Encoding.GetEncoding(1252).GetBytes(textBoxSend.Text);
            byte[] mRecv = new byte[2048];

            int ret = NICEVCATB(mSend, mRecv);
            MessageBox.Show(ret.ToString()); //리턴값 처리 꼭 해주세요.

            textBoxRecv.Text = System.Text.Encoding.Default.GetString(mRecv);

            
        }

        private void buttonCnl_Click(object sender, EventArgs e)
        {
            int ret = REQ_STOP();
        }

        private void button1_Click(object sender, EventArgs e)
        {
            byte[] mIp = System.Text.Encoding.GetEncoding(1252).GetBytes(ServerIp.Text);
            byte[] mPort = System.Text.Encoding.GetEncoding(1252).GetBytes(ServerPort.Text);

            int ret = Set_SvrInfo(mIp, mPort);
            MessageBox.Show(ret.ToString()); //리턴값 처리 꼭 해주세요.
        }

        private void button2_Click(object sender, EventArgs e)
        {
            //거래구분 : 0300 (포인트승인)
            //거래유형 : 10 (신용)
            //WCC : L (1차원바코드)
            //전문TEXT : PRO (PAYPRO)
            string FS = ((char)28).ToString();

            textBoxSend.Text = "0300" + FS + "10" + FS + "L" + FS + textMoney.Text + FS + "0" + FS + "0" + FS + "00" + FS + "" + FS + "" + FS + "" + FS + FS + FS + Barcode.Text + FS + FS + FS + FS + Textno.Text + FS + ApprFiller.Text + FS + FS + "PRO" + FS + "" + FS + ApprDealno.Text + FS + FS + FS + SignData.Text + FS;
    
            byte[] mSend = System.Text.Encoding.GetEncoding(1252).GetBytes(textBoxSend.Text);
            byte[] mRecv = new byte[2048];

            int ret = NICEVCATB(mSend, mRecv);
            MessageBox.Show(ret.ToString()); //리턴값 처리 꼭 해주세요.

            textBoxRecv.Text = System.Text.Encoding.Default.GetString(mRecv);

            int i = 0, j = 0, k = 0;
            string recvdata = (textBoxRecv.Text).ToString();
            
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
                            textAgreenum.Text = (textBox8.Text).Replace(" ", "");
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
                        case 22:
                            textBox22.Text = recvdata.Substring(k, i - k);
                            break;
                        case 23:
                            textBox23.Text = recvdata.Substring(k, i - k);
                            break;
                        case 24:
                            textBox24.Text = recvdata.Substring(k, i - k);
                            break;
                        case 25:
                            textBox25.Text = recvdata.Substring(k, i - k);
                            break;
                        case 26:
                            textBox26.Text = recvdata.Substring(k, i - k);
                            break;
                        case 27:
                            textBox27.Text = recvdata.Substring(k, i - k);
                            break;
                    }
                    k = i + 1;

                    if (j == 27)
                        break;
                }
                i = i + 1;
            }
        }

        private void button3_Click(object sender, EventArgs e)
        {
            //거래구분 : 0520 (포인트취소)
            //거래유형 : 10 (신용)
            //WCC : L (1차원바코드)
            //전문TEXT : PRO (PAYPRO)
            //원거래승인번호, 원거래승인날짜(YYMMDD) 필수
            string FS = ((char)28).ToString();

            textBoxSend.Text = "0520" + FS + "10" + FS + "L" + FS + textMoney.Text + FS + "0" + FS + "0" + FS + "00" + FS + textAgreenum.Text + FS + textAgreedate.Text + FS + "" + FS + FS + FS + Barcode.Text + FS + FS + FS + FS + Textno.Text + FS + ApprFiller.Text + FS + FS + "PRO" + FS + "" + FS + ApprDealno.Text + FS + FS + FS + SignData.Text + FS;
    
            byte[] mSend = System.Text.Encoding.GetEncoding(1252).GetBytes(textBoxSend.Text);
            byte[] mRecv = new byte[2048];

            int ret = NICEVCATB(mSend, mRecv);
            MessageBox.Show(ret.ToString()); //리턴값 처리 꼭 해주세요.

            textBoxRecv.Text = System.Text.Encoding.Default.GetString(mRecv);

            int i = 0, j = 0, k = 0;
            string recvdata = (textBoxRecv.Text).ToString();

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
                            textAgreenum.Text = (textBox8.Text).Replace(" ", "");
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
                        case 22:
                            textBox22.Text = recvdata.Substring(k, i - k);
                            break;
                        case 23:
                            textBox23.Text = recvdata.Substring(k, i - k);
                            break;
                        case 24:
                            textBox24.Text = recvdata.Substring(k, i - k);
                            break;
                        case 25:
                            textBox25.Text = recvdata.Substring(k, i - k);
                            break;
                        case 26:
                            textBox26.Text = recvdata.Substring(k, i - k);
                            break;
                        case 27:
                            textBox27.Text = recvdata.Substring(k, i - k);
                            break;
                    }
                    k = i + 1;

                    if (j == 27)
                        break;
                }
                i = i + 1;
            }
        }

        private void Form1_Load(object sender, EventArgs e)
        {
            textAgreedate.Text = DateTime.Now.ToString("yyMMdd");
        }
    }
}
