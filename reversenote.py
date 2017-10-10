# -*- coding: utf-8 -*-

import os
import requests
import hashlib
import urllib.parse
import json
import re


URL = 'http://malware.reversenote.info'
HOST = 'malware.reversenote.info'
URL_UPLOAD = 'http://%s/api.php?action=uploadfiles' % HOST
URL_UPDATE = 'http://%s/api.php?token=my_token&action=updatefile' % HOST


class ReverseNoteRepo:
    """Malware Repository Framework 를 이용한 자체 샘플 리포지터리 접근 클래스

    `다운로드`_ `공식문서`_ `공식문서(API)`_ `포럼`_

    .. _다운로드: https://www.adlice.com/download/mrf/
    .. _공식문서: https://www.adlice.com/documentation/mrf/documentation/
    .. _공식문서(API): https://www.adlice.com/documentation/mrf/documentation/#api
    .. _포럼: https://forum.adlice.com/index.php?board=10.0
    """

    def __init__(self, token):
        self.token = token
        self.url = urllib.parse.urljoin(URL, '/api.php')

    def downdload(self, md5str):
        """MD5 해쉬로 파일을 다운로드 한다

        :param md5str: md5 문자열
        :return:
        """

        if not isValidHash(md5str):
            raise ValueError('Invalid MD5 value \'%s\'' % md5str)

        # URL 세팅
        _get_param = (('token', self.token), ('action', 'downloadfile'), ('file', md5))
        _url = '?'.join([self.url, urllib.parse.urlencode(_get_param)])

        _res = requests.get(_url)
        if _res.status_code is 200:
            return _res.json()
        else:
            return False

    def upload(self, filetoupload, vtsubmit=False, tags='', comment=''):
        """파일을 업로드한다

        :param filetoupload: 업로드할 파일 Path
        :param vtsubmit: virustotal 업로드
        :param tags: 태그 문자열 (쉼표로 구분)
        :param comment: 코멘트 (not working)
        :return:
        """

        if os.stat(filetoupload).st_size > 32505856:  # over 31mb
            return False
        _filename = os.path.basename(filetoupload)

        # 파일정보 세팅
        _files_data = [{'index': 0, 'vtsubmit': vtsubmit, 'cksubmit': not vtsubmit, 'tags': tags}]
        _params = {'hash': md5(filetoupload), 'comment': comment, 'token': self.token, 'files_data': json.dumps(_files_data)}

        with open(filetoupload, 'rb') as fp:
            _files = {_filename: fp}
            _headers = {'user-agent': 'JW python script'}
            _res = requests.post(URL_UPLOAD, headers=_headers, files=_files, data=_params)

            if _res.status_code is 200:
                return _res.json()
            else:
                return False

    def delete(self, md5str):
        """동작안함

        :param md5str:
        :return:
        """
        # URL 세팅
        _get_param = (('token', self.token),
                      ('file', md5str))
        _url = '?'.join([self.url, urllib.parse.urlencode(_get_param)])

        _res = requests.get(_url)
        if _res.status_code is 200:
            return _res.json()

    def getfile(self, md5str):
        # URL 세팅
        _get_param = (('token', self.token), ('action', 'getfile'), ('hash', md5str))
        _url = '?'.join([self.url, urllib.parse.urlencode(_get_param)])

        _res = requests.get(_url)
        if _res.status_code is 200:
            return _res.json()
        else:
            return False

    def getfiles_by_tags(self, tags):
        # setup url
        _page = 0
        while True:
            _get_param = (('token', self.token), ('action', 'getfiles'), ('page', _page), ('tags', tags))
            _url = '?'.join([self.url, urllib.parse.urlencode(_get_param)])

            _res = requests.get(_url)

            if _res.status_code is 200:
                _result = _res.json()
                if not _result['files']:  # 결과 없음
                    break
                for file in _result['files']:
                    yield file
                _page += 1
            else:
                return None

    def update(self, md5str, desired_metadata):
        """메타정보를 업데이트한다

        업데이트하고 싶은 정보가 있다면, 정보를 받아와서 더해서 수정하는 식으로 진행할 것
        명시된 키값은, **덮어쓰기** 된다

        업데이트 가능항목은 주석 참고,
        API 설명상, 조회할때의 키와 업데이트 할 때의 키가 다르니 주의할것 (거지같음)

        :param md5str:
        :param desired_metadata:
        :return:
        """

        return False

        # URL 세팅
        _get_param = (('token', self.token), ('action', 'updatefile'))
        _url = '?'.join([self.url, urllib.parse.urlencode(_get_param)])

        # 파일정보 세팅
        _meta_org = self.getfile(md5str)
        _meta_org = _meta_org['file']
        _params = {'hash': md5str,
                   # 'favorite': _meta_org['favorite'],
                   # 'vendor': _meta_org['threat'],
                   # 'new_user': _meta_org['user_name'],
                   # 'comment': _meta_org['comment'],
                   # 'tags': tags,
                   # 'urls': _meta_org['urls'],
                   # 'lock': _meta_org['locked']
                   }
        # if 'vendor' in _meta_org:
        #     _params['vendor'] = _meta_org['vendor']

        _res = requests.post(_url, data=_params)

        if _res.status_code is 200:
            return _res.json()
        else:
            return False

    def add_tags(self, md5str, tags):
        """기존 태그에 태그를 추가한다

        :param md5str:
        :param tags:
        :return:
        """
        # URL 세팅
        _get_param = (('token', self.token), ('action', 'updatefile'))
        _url = '?'.join([self.url, urllib.parse.urlencode(_get_param)])

        # 파일정보 세팅
        _meta_org = self.getfile(md5str)
        _meta_org = _meta_org['file']
        _params = {'hash': md5str,
                   'tags': _meta_org['tags'] + ',%s' % tags,
                   }

        _res = requests.post(_url, data=_params)

        if _res.status_code is 200:
            return _res.json()
        else:
            return False

    def overwrite_tags(self, md5str, tags):
        """태그를 덮어쓴다

        :param md5str:
        :param tags:
        :return:
        """
        # URL 세팅
        _get_param = (('token', self.token), ('action', 'updatefile'))
        _url = '?'.join([self.url, urllib.parse.urlencode(_get_param)])

        # 파일정보 세팅
        _params = {'hash': md5str,
                   'tags': '%s' % tags,
                   }

        _res = requests.post(_url, data=_params)

        if _res.status_code is 200:
            return _res.json()
        else:
            return False

    def add_comment(self, md5str, comment):
        """기존 설명에 설명을 추가한다

        :param md5str:
        :param comment:
        :return:
        """
        # URL 세팅
        _get_param = (('token', self.token), ('action', 'updatefile'))
        _url = '?'.join([self.url, urllib.parse.urlencode(_get_param)])

        # 파일정보 세팅
        _meta_org = self.getfile(md5str)
        _meta_org = _meta_org['file']
        _params = {'hash': md5str,
                   'comment': _meta_org['comment'] + '\n' + comment
                   }

        _res = requests.post(_url, data=_params)

        if _res.status_code is 200:
            return _res.json()
        else:
            return False


def md5(filepath, blocksize=8192):
    """경로에 있는 파일의 MD5 해쉬 얻는다

    :param filepath: str, 파일 경로
    :param blocksize: int, 해쉬블럭
    :return: str, MD5 16진 문자열
    """

    md5 = hashlib.md5()

    fp = open(filepath, "rb")

    # 첫 블럭을 읽어온다
    buf = fp.read(blocksize)

    # 블럭이 없을 때까지 해쉬 업데이트
    while buf:
        md5.update(buf)
        buf = fp.read(blocksize)

    fp.close()

    # 계산된 값을 리턴
    return md5.hexdigest()


def isValidHash(hashStr, apikey=False):
    """해쉬문자열이 유효한지 검증한다

    :param hashStr: str()
    :param apikey: bool(), 검증할 문자열이 API key 일경우 True
    :return: bool()
    """

    patterns = [
        '^[a-fA-F0-9]{32}$',  # MD5
        '^[a-fA-F0-9]{40}$',  # SHA1
        '^[a-fA-F0-9]{64}$',  # SHA256 / Virustotal API Key
    ]

    if apikey:
        patterns = [patterns[2]]

    for pattern in patterns:
        match = re.match(pattern, hashStr)
        if match is not None:
            return True

    return False


if __name__ == '__main__':
    pass
