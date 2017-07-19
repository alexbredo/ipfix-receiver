# Copyright (c) 2014 Alexander Bredo
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or 
# without modification, are permitted provided that the 
# following conditions are met:
# 
# 1. Redistributions of source code must retain the above 
# copyright notice, this list of conditions and the following 
# disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above 
# copyright notice, this list of conditions and the following 
# disclaimer in the documentation and/or other materials 
# provided with the distribution.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND 
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, 
# INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF 
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE 
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR 
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, 
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES 
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE 
# GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR 
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF 
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT 
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT 
# OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE 
# POSSIBILITY OF SUCH DAMAGE.

import re

class SyntaxParser:
	RE_CHAR_TABULATOR = r"\t"
	RE_CHAR_SEMICOLON = r";"
	RE_CHAR_SPACES = r"\s+"
	RE_TIME = r"[0-2]\d:[0-5]\d(:[0-5]\d)?"
	RE_DATE_GERMAN = r"[0-3]\d.[0-1]\d.(\d{4}|\d{2})"
	RE_NUMBER = r"\d+(\.\d+)?"
	RE_WORD = r"[\w\d\-]+" # OLD: r"[\w\d]+"
	RE_NET_CIDR = r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}'
	RE_IPV4 = r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'
	RE_URL = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
	RE_DOMAIN = r'([\w]+\.)?[a-z,A-Z,0-9\-]+\.[a-zA-Z]{2,3}'
	RE_EMAIL = r'[\w]+@[a-z,A-Z,0-9\-\.\_]+\.[a-zA-Z]{2,3}'
	
	def __init__(self):
		self.scanner = re.Scanner([
		  (SyntaxParser.RE_CHAR_SEMICOLON,	lambda scanner,token:("SEMICOLON", token)),
		  (SyntaxParser.RE_CHAR_TABULATOR,	lambda scanner,token:("TABULATOR", token)),
		  (SyntaxParser.RE_NET_CIDR,		lambda scanner,token:("NET_CIDR", token)),
		  (SyntaxParser.RE_IPV4,			lambda scanner,token:("IPV4", token)),
		  (SyntaxParser.RE_URL,				lambda scanner,token:("URL", token)),
		  (SyntaxParser.RE_EMAIL,			lambda scanner,token:("EMAIL", token)),
		  (SyntaxParser.RE_DOMAIN,			lambda scanner,token:("DOMAIN", token)),
		  (SyntaxParser.RE_TIME,			lambda scanner,token:("TIME", token)),
		  (SyntaxParser.RE_DATE_GERMAN,		lambda scanner,token:("DATE_GERMAN", token)),
		  (SyntaxParser.RE_NUMBER,			lambda scanner,token:("NUMBER", token)),
		  (SyntaxParser.RE_WORD,			lambda scanner,token:("WORD", token)),
		  (SyntaxParser.RE_CHAR_SPACES,		None), # None == skip token.
		  (r'.', lambda scanner, token: None), # Skip everything else
		])
		
	def getTokens(self, phrase):
		return self.scanner.scan(phrase)[0]