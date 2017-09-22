#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from telepot import Bot, glance
try:
    from cStringIO import StringIO      # Python 2 compatible
except ImportError:
    from io import StringIO


CRITICAL = logging.CRITICAL  # 50
ERROR = logging.ERROR  # 40
WARNING = logging.WARNING  # 30
INFO = logging.INFO  # 20
DEBUG = logging.DEBUG  # 10
NOTSET = logging.NOTSET  # 0


_MAX_BYTES = 5*1024*1024
_MAX_BACKUP = 5


class _Telegram:
    """Telegram 봇 관리 클래스"""

    def __init__(self, token):
        """
        봇 초기화 및 메시지루프 등록

        봇은 botfather 을 통해 등록가능
        자세한 사용법은 여기 참고
        https://core.telegram.org/bots/api
        # TODO: 링크추가

        :param token: 텔레그램 봇 API 키
        :type token: str
        """
        self.bot = Bot(token)
        self.bot.message_loop(self.msg_handler)

        self.chat_ids = set([])  # 메시지를 전송할 chat_id 리스트(set([]) 는 리스트와 동일하게 사용가능)

    def send_log(self, msg):
        """등록한 모든 사용자에게 로그 전송

        :param msg:
        :return:
        """
        for chat_id in self.chat_ids:
            self.send_msg(chat_id, msg)

    def send_msg(self, chat_id, msg):
        """해당하는 id에 메시지 전송

        :param chat_id:
        :param msg:
        :return:
        """
        self.bot.sendMessage(chat_id, msg)

    def msg_handler(self, msg):
        """메시지 핸들러

        콜백으로 동작한다
        :param msg:
        :return:
        """
        # 사용자가 보내온 메시지 정리
        content_type, chat_type, chat_id = glance(msg)

        # 보낸 메시지가 텍스트라면 echo
        if content_type is 'text':
            if msg['text'] == '/enter':
                self.chat_ids.add(chat_id)
                self.send_msg(chat_id, 'Your chat_id(%d) is registered to Telelogram' % chat_id)
                self.send_msg(chat_id, 'current users: %d' % len(self.chat_ids))
            elif msg['text'] == '/exit':
                self.chat_ids.remove(chat_id)
                self.send_msg(chat_id, 'Your chat_id(%d) is deleted from Telelogram' % chat_id)
                self.send_msg(chat_id, 'current users: %d' % len(self.chat_ids))
            else:
                self.bot.sendMessage(chat_id, 'You said \'%s\'' % msg['text'])


class _TelegramHandler(logging.StreamHandler):
    """텔레그램 메시지 전송을 위한 로그메시지 핸들러"""
    def __init__(self, apikey=None):
        super().__init__(None)

        # 텔레그램 메시지 전송용 클래스 생성
        self.telegram = _Telegram(apikey)

    def emit(self, record):
        """
        Emit a record.

        If a formatter is specified, it is used to format the record.
        The record is then written to the stream with a trailing newline.  If
        exception information is present, it is formatted using
        traceback.print_exception and appended to the stream.  If the stream
        has an 'encoding' attribute, it is used to determine how to do the
        output to the stream.
        """
        try:
            # 로그메시지 수신
            msg = self.format(record)

            # 텔레그램에 전달
            self.telegram.send_log(msg)
            self.flush()
        except Exception:
            self.handleError(record)


def setup_log(logpath=None, logname=NOTSET, loglevel=DEBUG, apikey=None):
    """
    전역로거를 설치한다

    로거는 '이름'으로 접근할 수 있다
    이름을 명시하지 않으면, 'root' 로거를 WARNING 레벨로 자동으로 가져온다
    'root' 로거 사용시 파이썬 내장 모듈의 로그도 같이 뜰 것이니 주의

    logging.getLogger('MyLoggerName').debug('My debug msg') 와 같이
    한번 설치한 로거를 어디서든 쓸 수 있다

    로그 메시지는 하나의 로거에 '핸들러'를 추가해
    로거에 전달된 메시지를 각각의 핸들러가 포맷과 출력기기에 맞게 출력해주는 방식

    logpath 명시 안하면, stderr 로만 로그를 출력한다
    텔레그램 봇이 없다고? apikey 를 생략하면 된다

    :param logpath: 로그파일 저장경로(파일명 포함)
    :type logpath: str
    :param logname: 로거 이름
    :type logname: str
    :param loglevel: 로그 레벨
    :type loglevel: int
    :param apikey: 텔레그램 봇 api키
    :type apikey: str
    """
    # logger 인스턴스를 생성
    _logger = logging.getLogger(logname)

    # 로깅 레벨 설정
    _logger.setLevel(loglevel)

    # 로그 포맷 설정
    _formatter = logging.Formatter('[%(levelname)s|%(filename)s:%(lineno)s] %(asctime)s > %(message)s')

    # 로그파일 경로가 명시된 경우 저장경로 세팅 (로그를 파일로도 저장하는 경우)
    _log_path = None
    _file = None
    if isinstance(logpath, str):
        _main_path = os.path.dirname(os.path.abspath(sys.modules['__main__'].__file__))
        _log_path = os.path.join(_main_path, logpath)  # (원본실행위치 + 상대경로)

    # 로깅 핸들러 설정
    if _log_path:  # 파일저장용 핸들러
        _file = RotatingFileHandler(_log_path, mode='a', maxBytes=_MAX_BYTES, backupCount=_MAX_BACKUP)
    _stderr = logging.StreamHandler()  # stderr 출력용 핸들러
    _telegram = _TelegramHandler(apikey)  # Telegram 전송용 핸들러

    # specify handler's logging format
    if _log_path:
        _file.setFormatter(_formatter)
    _stderr.setFormatter(_formatter)
    _telegram.setFormatter(_formatter)

    # set Handler to logger
    if _log_path:
        _logger.addHandler(_file)
    _logger.addHandler(_stderr)
    _logger.addHandler(_telegram)

    if _log_path:
        _logger.debug('Logger initiated, log file path is \'%s\'' % _log_path)
    else:
        _logger.debug('Logger initiated as fileless mode')


def __how_to_use():
    """
    사용예제

    1. botFather 에서 봇 생성
    2. @my_bot 대화창을 열고 대기한다
    3. setup_log(logname='mylogger', loglevel=DEBUG, apikey='MY_API_KEY')
    4. @my_bot 대화창에서 '/enter' 입력
    5. logging.getLogger('mylogger').debug('My debug msg')  # 어디서든 이 형태로 출력 가능
    :return:
    """
    setup_log(logname='mylogger', loglevel=DEBUG, apikey='MY_API_KEY')

    while True:
        msg = input('type any: ')
        logging.getLogger('mylogger').debug(str(msg))


if __name__ == '__main__':
    pass

