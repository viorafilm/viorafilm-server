var ws;
var ws2;
var conninfo;
//status : 현재 상태
var status = 5;
var sendbuf;
var rtndata;

String.prototype.NCbyteLength = function(){
	var l=0;
	
	for(var idx = 0; idx < this.length; idx++){
		var c = escape(this.charAt(idx));

		if(c.length == 1) l++;
		else if(c.indexOf("%u") != -1) l += 3;
		else if(c.indexOf("%") != -1) l += c.length/3; //JDK20210427 : UTF-8기준. EUC-KR은 /2로 수정 필요.
	}
	
	return l;
};


function NCpad(n,width)
{
	n = n + '';
	return n.length >= width ? n : new Array(width - n.length + 1).join('0') + n;
}

function POSSEND(port, type, senddata, callback)  
{
//port: 로컬 데몬 PORT, type : (PCAT -> postocat , VCAT -> NVCAT) , senddata : 거래 요청 데이터, callback : 응답 CallBack 함수
	//svrport = "50001";
	if(status != 5)
		return ;
	status = 0;
	
	sendbuf = make_send_data(type,senddata);
	
	conninfo = "ws://localhost:" + port + "/" + type;
		
	if ("WebSocket" in window) {
		ws = new WebSocket(conninfo);
		ws.onopen = function(event) {
			//연결성공
			status = 1;
			alert(sendbuf);
			ws_send_data(ws,sendbuf);
		};

		ws.onerror = function(event) {
			//연결실패
			status = 6;
			//callback(-1,"");
			return false;
		};

		ws.onmessage = function(event) {
			//응답수신
			status = 3;
			ws_disconnect(ws);
			parse_recv_data(event.data,callback);
			//callback(0,event.data);
		};

		ws.onclose = function(event) {
			status = 5;
			//연결종료
		};
	} else {
		//브라우저가 webSocket을 지원하지 않음.
		return false;
	}
}

function ReqStop(port,type)  
{
	if(status != 1 && status != 2) return;
	
	port = Number(port) + 1; //Stop 포트번호 1 높음
	
	conninfo = "ws://localhost:" + port + "/" + type;
	
	if ("WebSocket" in window) {
		ws2 = new WebSocket(conninfo);
		ws2.onopen = function(event) {
			//연결성공
			ws_send_data(ws2,make_send_data(type,"STOP"));
		};

		ws2.onerror = function(event) {
			//연결실패
			return false;
		};

		ws2.onmessage = function(event) {
			//응답수신
			status = 3;
			//ws_disconnect(ws2);	
			//parse_recv_data(event.data,callback);
			//callback(0,event.data);
		};

		ws2.onclose = function(event) {
			ws_disconnect(ws2);
			status = 6;
			//연결종료
		};
	} else {
		//브라우저가 webSocket을 지원하지 않음.
		return false;
	}	
}

function ws_disconnect(aws) {
	status = 4;
	aws.close();
}

function ws_send_data(aws,sendbuf) {	
	
	status = 2;		
	aws.send(sendbuf);	
	
	return false;
}

function make_send_data(type, senddata) {
	var m_sendmsg;
	var m_totlen;
	var m_bodylen;
	
	m_bodylen = senddata.NCbyteLength();
	m_totlen = 12 + m_bodylen;
	
	if(type == 'NICEVCAT')
	{
		return NCpad(m_totlen,4) + type + NCpad(m_bodylen,4) + senddata;
	}
	else
		return NCpad(m_totlen,4) + type + "    " + NCpad(m_bodylen,4) + senddata;
	//return '0031VCAT    0019REQ_SELECTBTN2가'
}

function parse_recv_data(recvdata, callback) {
	var rtndata;
	var bodylen;
	
	bodylen = recvdata.substr(12,4);
	
	if(recvdata.substr(8,4) != "0000")
	{
		//오류코드 매핑!!
		 /*
		 //NVCAT
		 1 : 정상
		-1 : NVCAT 실행 중이 아님
		-2 : 거래금액이 존재하지 않음
		-3 : 환경정보 읽기 실패
		-4 : NVCAT 연동오류 실패
		-5 : 기타 응답데이터 오류
		-6 : 카드리딩 타임아웃
		-7 : 사용자 및 리더기 취소
		-8 : FALLBACK 거래요청
		-9 : 기타오류
		-10 :IC우선거래 요청
		-11 : FALLBACK 거래 아님
		-12 : 거래불가카드
		-13 : 서명요청 오류
		-14 : 요청 전문 데이터 오류
		-15 : 카드리더 Port Open 오류
		
		 //PCAT
		 1 : 정상
		-1 : 포트 오픈 실패
		-2 : 포트 이미 오픈된 상태
		-3 : ACK 수신 실패 (단말기 연결 실패)
		-4 : LRC오류 OR 종료버튼
		-14 : 요청 전문 데이터 오류
		*/	
		
		var errcd;
		
		errcd = recvdata.substr(8,4) * -1
		
		callback(errcd,recvdata);
	}else
	{
		//callback(1,recvdata.substr(16,bodylen));
		//VCAT 요청일 경우     : TotalLen(4) + "VCAT" + ReturnCode(4) + DataSize(4) + Data
		//NICEVCAT 요청일 경우 : TotalLen(4) + "VCAT" + ReturnCode(4) + DataSize(4) + Data
		callback(1,recvdata);
	}
}
