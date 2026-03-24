using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Windows.Forms;
using System.Runtime.InteropServices;

namespace NicePosICV105
{
    public partial class Form1 : Form
    {
        [DllImport("NVCAT.dll", CharSet = CharSet.Unicode)]
        static extern long NICEVCAT(byte[] send_data, byte[] recv_data); //NVCAT 결제 요청

        [DllImport("NVCAT.dll", CharSet = CharSet.Unicode)]
        static extern void CallBackReg(Callback_Function callback); //CALLBACK 함수 등록

        [DllImport("NVCAT.dll", CharSet = CharSet.Unicode)]
        public static extern int ReaderPortOpen(); //리더기 포트 OPEN 함수 (OpenPort)

        [DllImport("NVCAT.dll", CharSet = CharSet.Unicode)]
        public static extern int ReaderPortClose(); //리더기 포트 CLOSE 함수 (ClosePort)

        [DllImport("NVCAT.dll", CharSet = CharSet.Unicode)]
        static extern long REQ_STOP(); //카드리더기 요청 취소


        Callback_Function callback_func;
        delegate void Callback_Function(int a);

        string FS = ((char)28).ToString(); //FS

        byte[] mRecvData = new byte[4096];
        byte[] mSendData = new byte[4096];
        long ret, rtn;

        void Ptest(int val)
        {
            MessageBox.Show("이벤트 구분값 : " + val);

            switch (val)
            {
                case 1: //IC카드가 삽입 되었음
                    MessageBox.Show("IC카드가 삽입 되었음");
                    {
                        ret = ReaderPortClose(); //4. 이벤트 구분 값 수신 후 카드리더기 PORT CLOSE

                        mSendData = Encoding.GetEncoding(51949).GetBytes("0200" + FS + "10" + FS + "C" + FS + "1004" + FS + FS + FS + "00" + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS);
                        rtn = NICEVCAT(mSendData, mRecvData); //5. 이벤트 구분 값에 따라 NVCAT 결제 요청

                        if (rtn > 0)
                        {
                            MessageBox.Show(Encoding.Default.GetString(mRecvData));
                            textRecvdata.Text = Encoding.Default.GetString(mRecvData);
                        }

                        ret = ReaderPortOpen(); //6. 결제 완료 후 카드리더기 PORT OEPN 후 카드리딩 대기 
                    }
                    break;

                case 2: //리더기 해킹 (리더기 사용불가)
                    MessageBox.Show("리더기 해킹 (리더기 사용불가)");
                    MessageBox.Show("카드리더기 무결성 오류! (카드리더기 교체 필요)"); 
                    break;

                case 3: //MS카드 리딩 이벤트 (IC 승인요청 해야함) 
                    MessageBox.Show("MS카드 리딩 이벤트 (IC 승인요청 해야함)");
                    MessageBox.Show("IC카드 우선거래 필요!");
                    {
                        ret = ReaderPortClose(); //4. 이벤트 구분 값 수신 후 카드리더기 PORT CLOSE

                        mSendData = Encoding.GetEncoding(51949).GetBytes("0200" + FS + "10" + FS + "C" + FS + "1004" + FS + FS + FS + "00" + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS);
                        rtn = NICEVCAT(mSendData, mRecvData); //5. 이벤트 구분 값에 따라 NVCAT 결제 요청

                        if (rtn > 0)
                        {
                            MessageBox.Show(Encoding.Default.GetString(mRecvData));
                            textRecvdata.Text = Encoding.Default.GetString(mRecvData);
                        }

                        ret = ReaderPortOpen(); //6. 결제 완료 후 카드리더기 PORT OEPN 후 카드리딩 대기 
                    }
                    break;

                case 4: //MS카드 리딩 이벤트 (MS 승인처리 가능)
                    MessageBox.Show("MS카드 리딩 이벤트 (MS 승인처리 가능)");
                    MessageBox.Show("MS Only 카드 리딩!");
                    {
                        ret = ReaderPortClose(); //4. 이벤트 구분 값 수신 후 카드리더기 PORT CLOSE

                        mSendData = Encoding.GetEncoding(51949).GetBytes("0200" + FS + "10" + FS + "C" + FS + "1004" + FS + FS + FS + "00" + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS);
                        rtn = NICEVCAT(mSendData, mRecvData); //5. 이벤트 구분 값에 따라 NVCAT 결제 요청

                        if (rtn > 0)
                        {
                            MessageBox.Show(Encoding.Default.GetString(mRecvData));
                            textRecvdata.Text = Encoding.Default.GetString(mRecvData);
                        }

                        ret = ReaderPortOpen(); //6. 결제 완료 후 카드리더기 PORT OEPN 후 카드리딩 대기 
                    }
                    break;

                case 5: //리더기 오동작 (잘못된 명령어 인식)
                    MessageBox.Show("리더기 오동작 (잘못된 명령어 인식)");
                    MessageBox.Show("카드리더기 오류!");
                    break;

                case 6: //IC카드가 리더기에 삽입. CHIP 불량 (FALLBACK 거래 유도)
                    MessageBox.Show("IC카드가 리더기에 삽입. CHIP 불량 (FALLBACK 거래 유도)");
                    MessageBox.Show("FALLBACK 거래 필요!");
                    {
                        ret = ReaderPortClose(); //4. 이벤트 구분 값 수신 후 카드리더기 PORT CLOSE

                        mSendData = Encoding.GetEncoding(51949).GetBytes("0200" + FS + "10" + FS + "F" + FS + "1004" + FS + FS + FS + "00" + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS);
                        rtn = NICEVCAT(mSendData, mRecvData); //5. 이벤트 구분 값에 따라 NVCAT 결제 요청

                        if (rtn > 0)
                        {
                            MessageBox.Show(Encoding.Default.GetString(mRecvData));
                            textRecvdata.Text = Encoding.Default.GetString(mRecvData);
                        }

                        ret = ReaderPortOpen(); //6. 결제 완료 후 카드리더기 PORT OEPN 후 카드리딩 대기 
                    }
                    break;

                case 7: //해외 은련 AID 이벤트 (은련 IC 거래 유도, 메세지 출력 후 초기화 처리)
                    MessageBox.Show("해외 은련 AID 이벤트 (은련 IC 거래 유도, 메세지 출력 후 초기화 처리)");
                    MessageBox.Show("해외 은련 카드!");

                    {
                        ret = ReaderPortClose(); //4. 이벤트 구분 값 수신 후 카드리더기 PORT CLOSE

                        mSendData = Encoding.GetEncoding(51949).GetBytes("0200" + FS + "UP" + FS + "C" + FS + "1004" + FS + FS + FS + "00" + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS);
                        rtn = NICEVCAT(mSendData, mRecvData); //5. 이벤트 구분 값에 따라 NVCAT 결제 요청

                        if (rtn > 0)
                        {
                            MessageBox.Show(Encoding.Default.GetString(mRecvData));
                            textRecvdata.Text = Encoding.Default.GetString(mRecvData);
                        }

                        ret = ReaderPortOpen(); //6. 결제 완료 후 카드리더기 PORT OEPN 후 카드리딩 대기 
                    }
                    break;

                case 8: //현금IC 카드 AID 이벤트 (현금IC 거래 유도)
                    MessageBox.Show("현금IC 카드 AID 이벤트 (현금IC 거래 유도)");
                    if (MessageBox.Show("현금 IC 계좌가 존재 합니다.\n현금 IC카드로 결제 하시겠습니까?", "현금 IC카드!", MessageBoxButtons.YesNo) == DialogResult.Yes)
                    {
                        ret = ReaderPortClose(); //4. 이벤트 구분 값 수신 후 카드리더기 PORT CLOSE

                        mSendData = Encoding.GetEncoding(51949).GetBytes("0200" + FS + "I1" + FS + "01" + FS + FS + FS + "1004" + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS);
                        rtn = NICEVCAT(mSendData, mRecvData);

                        if (rtn > 0)
                        {
                            MessageBox.Show(Encoding.Default.GetString(mRecvData));
                            textRecvdata.Text = Encoding.Default.GetString(mRecvData);
                        }

                        ret = ReaderPortOpen();
                        break;
                    }
                    else
                    {
                        ret = ReaderPortClose(); //4. 이벤트 구분 값 수신 후 카드리더기 PORT CLOSE

                        mSendData = Encoding.GetEncoding(51949).GetBytes("0200" + FS + "10" + FS + "C" + FS + "1004" + FS + FS + FS + "00" + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS + FS);
                        rtn = NICEVCAT(mSendData, mRecvData); //5. 이벤트 구분 값에 따라 NVCAT 결제 요청

                        if (rtn > 0)
                        {
                            MessageBox.Show(Encoding.Default.GetString(mRecvData));
                            textRecvdata.Text = Encoding.Default.GetString(mRecvData);
                        }

                        ret = ReaderPortOpen(); //6. 결제 완료 후 카드리더기 PORT OEPN 후 카드리딩 대기 
                        break;
                    }

                case 9: //거래 불가 카드
                    MessageBox.Show("거래 불가 카드!");
                    break;
            }
 
        }

        public Form1()
        {
            InitializeComponent();
        }

        private void Form1_Load(object sender, EventArgs e)
        {
            CheckForIllegalCrossThreadCalls = false; //크로스 스레드 사용을 위해 FALSE
        }

        private void Form1_FormClosing(object sender, FormClosingEventArgs e)
        {
            
        }

        private void button12_Click(object sender, EventArgs e) //1. 콜백 함수 등록
        {
            callback_func = new Callback_Function(Ptest);
            CallBackReg(callback_func);
        }

        private void button10_Click(object sender, EventArgs e) //2. 카드리더기 PORT OEPN
        {
            int ret = ReaderPortOpen(); 
        }

        private void button11_Click(object sender, EventArgs e)
        {
            int ret = ReaderPortClose();
        }

        private void button13_Click_1(object sender, EventArgs e)
        {
            REQ_STOP();
        }
    }
}
