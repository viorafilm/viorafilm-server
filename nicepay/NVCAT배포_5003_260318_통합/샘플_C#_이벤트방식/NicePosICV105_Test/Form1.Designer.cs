namespace NicePosICV105
{
    partial class Form1
    {
        /// <summary>
        /// 필수 디자이너 변수입니다.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        /// 사용 중인 모든 리소스를 정리합니다.
        /// </summary>
        /// <param name="disposing">관리되는 리소스를 삭제해야 하면 true이고, 그렇지 않으면 false입니다.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form 디자이너에서 생성한 코드

        /// <summary>
        /// 디자이너 지원에 필요한 메서드입니다.
        /// 이 메서드의 내용을 코드 편집기로 수정하지 마십시오.
        /// </summary>
        private void InitializeComponent()
        {
            this.button12 = new System.Windows.Forms.Button();
            this.button10 = new System.Windows.Forms.Button();
            this.button11 = new System.Windows.Forms.Button();
            this.button13 = new System.Windows.Forms.Button();
            this.label10 = new System.Windows.Forms.Label();
            this.textRecvdata = new System.Windows.Forms.TextBox();
            this.label3 = new System.Windows.Forms.Label();
            this.SuspendLayout();
            // 
            // button12
            // 
            this.button12.Font = new System.Drawing.Font("Malgun Gothic", 9F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(129)));
            this.button12.Location = new System.Drawing.Point(15, 15);
            this.button12.Name = "button12";
            this.button12.Size = new System.Drawing.Size(298, 23);
            this.button12.TabIndex = 26;
            this.button12.Text = "콜백함수등록 (CallBackReg)";
            this.button12.UseVisualStyleBackColor = true;
            this.button12.Click += new System.EventHandler(this.button12_Click);
            // 
            // button10
            // 
            this.button10.Font = new System.Drawing.Font("Malgun Gothic", 9F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(129)));
            this.button10.Location = new System.Drawing.Point(15, 44);
            this.button10.Name = "button10";
            this.button10.Size = new System.Drawing.Size(298, 23);
            this.button10.TabIndex = 27;
            this.button10.Text = "카드리더기 Port Open (ReaderPortOpen)";
            this.button10.UseVisualStyleBackColor = true;
            this.button10.Click += new System.EventHandler(this.button10_Click);
            // 
            // button11
            // 
            this.button11.Font = new System.Drawing.Font("Malgun Gothic", 9F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(129)));
            this.button11.Location = new System.Drawing.Point(15, 73);
            this.button11.Name = "button11";
            this.button11.Size = new System.Drawing.Size(298, 23);
            this.button11.TabIndex = 28;
            this.button11.Text = "카드리더기 Port Close (ReaderPortClose)";
            this.button11.UseVisualStyleBackColor = true;
            this.button11.Click += new System.EventHandler(this.button11_Click);
            // 
            // button13
            // 
            this.button13.Font = new System.Drawing.Font("Malgun Gothic", 9F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(129)));
            this.button13.Location = new System.Drawing.Point(15, 102);
            this.button13.Name = "button13";
            this.button13.Size = new System.Drawing.Size(298, 23);
            this.button13.TabIndex = 29;
            this.button13.Text = "카드리딩 요청취소 (REQ_STOP)";
            this.button13.UseVisualStyleBackColor = true;
            this.button13.Click += new System.EventHandler(this.button13_Click_1);
            // 
            // label10
            // 
            this.label10.AutoSize = true;
            this.label10.Location = new System.Drawing.Point(316, 15);
            this.label10.Name = "label10";
            this.label10.Size = new System.Drawing.Size(324, 105);
            this.label10.TabIndex = 40;
            this.label10.Text = "NVCAT 이벤트 처리 방식 사용 방법\r\n1. 콜백 함수 등록\r\n2. 카드리더기 PORT OEPN\r\n3. 카드 이벤트\r\n4. 이벤트 구분 값 수신" +
    " 후 카드리더기 PORT CLOSE\r\n5. 이벤트 구분 값에 따라 NVCAT 결제 요청\r\n6. 결제 완료 후 카드리더기 PORT OEPN 후 카" +
    "드리딩 대기 \r\n";
            // 
            // textRecvdata
            // 
            this.textRecvdata.Font = new System.Drawing.Font("Malgun Gothic", 8.25F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(129)));
            this.textRecvdata.Location = new System.Drawing.Point(85, 131);
            this.textRecvdata.Name = "textRecvdata";
            this.textRecvdata.Size = new System.Drawing.Size(544, 22);
            this.textRecvdata.TabIndex = 41;
            // 
            // label3
            // 
            this.label3.AutoSize = true;
            this.label3.Location = new System.Drawing.Point(12, 134);
            this.label3.Name = "label3";
            this.label3.Size = new System.Drawing.Size(67, 15);
            this.label3.TabIndex = 42;
            this.label3.Text = "응답데이터";
            // 
            // Form1
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(7F, 15F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(641, 167);
            this.Controls.Add(this.label3);
            this.Controls.Add(this.textRecvdata);
            this.Controls.Add(this.label10);
            this.Controls.Add(this.button13);
            this.Controls.Add(this.button11);
            this.Controls.Add(this.button10);
            this.Controls.Add(this.button12);
            this.Font = new System.Drawing.Font("Malgun Gothic", 9F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(129)));
            this.FormBorderStyle = System.Windows.Forms.FormBorderStyle.FixedDialog;
            this.Margin = new System.Windows.Forms.Padding(3, 4, 3, 4);
            this.MaximizeBox = false;
            this.Name = "Form1";
            this.SizeGripStyle = System.Windows.Forms.SizeGripStyle.Hide;
            this.Text = "NVCAT TEST (카드리더기 이벤트 처리방식)";
            this.FormClosing += new System.Windows.Forms.FormClosingEventHandler(this.Form1_FormClosing);
            this.Load += new System.EventHandler(this.Form1_Load);
            this.ResumeLayout(false);
            this.PerformLayout();

        }

        #endregion

        private System.Windows.Forms.Button button12;
        private System.Windows.Forms.Button button10;
        private System.Windows.Forms.Button button11;
        private System.Windows.Forms.Button button13;
        private System.Windows.Forms.Label label10;
        private System.Windows.Forms.TextBox textRecvdata;
        private System.Windows.Forms.Label label3;
    }
}

