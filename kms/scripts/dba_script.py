#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License. See accompanying LICENSE file.
#

import os
import re
import sys
import errno
import shlex
import logging
import platform
import subprocess
import fileinput
import getpass
from os.path import basename
from subprocess import Popen,PIPE
from datetime import date
globalDict = {}

os_name = platform.system()
os_name = os_name.upper()

if os_name == "LINUX":
        RANGER_KMS_HOME = os.getcwd()
elif os_name == "WINDOWS":
        RANGER_KMS_HOME = os.getenv("RANGER_KMS_HOME")

def call_keystore(libpath,aliasKey,aliasValue , filepath,getorcreate):
    finalLibPath = libpath.replace('\\','/').replace('//','/')
    finalFilePath = 'jceks://file/'+filepath.replace('\\','/').replace('//','/')
    if getorcreate == 'create':
        commandtorun = ['java', '-cp', finalLibPath, 'org.apache.ranger.credentialapi.buildks' ,'create', aliasKey, '-value', aliasValue, '-provider',finalFilePath]
        p = Popen(commandtorun,stdin=PIPE, stdout=PIPE, stderr=PIPE)
        output, error = p.communicate()
        statuscode = p.returncode
        return statuscode
    elif getorcreate == 'get':
        commandtorun = ['java', '-cp', finalLibPath, 'org.apache.ranger.credentialapi.buildks' ,'get', aliasKey, '-provider',finalFilePath]
        p = Popen(commandtorun,stdin=PIPE, stdout=PIPE, stderr=PIPE)
        output, error = p.communicate()
        statuscode = p.returncode
        return statuscode, output
    else:
        print 'proper command not received for input need get or create'


def check_output(query):
	if os_name == "LINUX":
		p = subprocess.Popen(shlex.split(query), stdout=subprocess.PIPE)
	elif os_name == "WINDOWS":
		p = subprocess.Popen(query, stdout=subprocess.PIPE, shell=True)
	output = p.communicate ()[0]
	return output

def log(msg,type):
	if type == 'info':
		logging.info(" %s",msg)
	if type == 'debug':
		logging.debug(" %s",msg)
	if type == 'warning':
		logging.warning(" %s",msg)
	if type == 'exception':
		logging.exception(" %s",msg)
	if type == 'error':
		logging.error(" %s",msg)

def populate_global_dict():
	global globalDict
	if os_name == "LINUX":
		read_config_file = open(os.path.join(RANGER_KMS_HOME,'install.properties'))
	elif os_name == "WINDOWS":
		read_config_file = open(os.path.join(RANGER_KMS_HOME,'bin','install_config.properties'))
	library_path = os.path.join(RANGER_KMS_HOME,"cred","lib","*")
	read_config_file = open(os.path.join(os.getcwd(),'install.properties'))
	for each_line in read_config_file.read().split('\n') :
		if len(each_line) == 0 : continue
		if re.search('=', each_line):
			key , value = each_line.strip().split("=",1)
			key = key.strip()
			if 'PASSWORD' in key:
				jceks_file_path = os.path.join(RANGER_KMS_HOME, 'jceks','ranger_db.jceks')
				statuscode,value = call_keystore(library_path,key,'',jceks_file_path,'get')
				if statuscode == 1:
					value = ''
			value = value.strip()
			globalDict[key] = value

def logFile(msg):
	if globalDict["dryMode"]==True:
		logFileName=globalDict["dryModeOutputFile"]
		if logFileName !="":
			if os.path.isfile(logFileName):
				if os.access(logFileName, os.W_OK):
					with open(logFileName, "a") as f:
						f.write(msg+"\n")
						f.close()
				else:
					print("Unable to open file "+logFileName+" in write mode, Check file permissions.")
					sys.exit()
			else:
				print(logFileName+" is Invalid input file name! Provide valid file path to write DBA scripts:")
				sys.exit()
		else:
			print("Invalid input! Provide file path to write DBA scripts:")
			sys.exit()

class BaseDB(object):

	def create_rangerdb_user(self, root_user, db_user, db_password, db_root_password,dryMode):
		log("[I] ---------- Creating user ----------", "info")

	def check_connection(self, db_name, db_user, db_password):
		log("[I] ---------- Verifying DB connection ----------", "info")

	def create_db(self, root_user, db_root_password, db_name, db_user, db_password,dryMode):
		log("[I] ---------- Verifying database ----------", "info")



class MysqlConf(BaseDB):
	# Constructor
	def __init__(self, host,SQL_CONNECTOR_JAR,JAVA_BIN):
		self.host = host
		self.SQL_CONNECTOR_JAR = SQL_CONNECTOR_JAR
		self.JAVA_BIN = JAVA_BIN

	def get_jisql_cmd(self, user, password ,db_name):
		#TODO: User array for forming command
		path = os.getcwd()
		if os_name == "LINUX":
			jisql_cmd = "%s -cp %s:jisql/lib/* org.apache.util.sql.Jisql -driver mysqlconj -cstring jdbc:mysql://%s/%s -u %s -p %s -noheader -trim -c \;" %(self.JAVA_BIN,self.SQL_CONNECTOR_JAR,self.host,db_name,user,password)
		elif os_name == "WINDOWS":
			self.JAVA_BIN = self.JAVA_BIN.strip("'")
			jisql_cmd = "%s -cp %s;%s\jisql\\lib\\* org.apache.util.sql.Jisql -driver mysqlconj -cstring jdbc:mysql://%s/%s -u %s -p %s -noheader -trim" %(self.JAVA_BIN, self.SQL_CONNECTOR_JAR, path, self.host, db_name, user, password)
		return jisql_cmd

	def verify_user(self, root_user, db_root_password, host, db_user, get_cmd,dryMode):
		if dryMode == False:
			log("[I] Verifying user " + db_user+ " for Host "+ host, "info")
		if os_name == "LINUX":
			query = get_cmd + " -query \"select user from mysql.user where user='%s' and host='%s';\"" %(db_user,host)
		elif os_name == "WINDOWS":
			query = get_cmd + " -query \"select user from mysql.user where user='%s' and host='%s';\" -c ;" %(db_user,host)
		output = check_output(query)
		if output.strip(db_user + " |"):
			return True
		else:
			return False

	def check_connection(self, db_name, db_user, db_password):
		#log("[I] Checking connection..", "info")
		get_cmd = self.get_jisql_cmd(db_user, db_password, db_name)
		if os_name == "LINUX":
			query = get_cmd + " -query \"SELECT version();\""
		elif os_name == "WINDOWS":
			query = get_cmd + " -query \"SELECT version();\" -c ;"
		output = check_output(query)
		if output.strip('Production  |'):
			#log("[I] Checking connection passed.", "info")
			return True
		else:
			log("[E] Can't establish db connection.. Exiting.." ,"error")
			sys.exit(1)

	def create_rangerdb_user(self, root_user, db_user, db_password, db_root_password,dryMode):
		if self.check_connection('mysql', root_user, db_root_password):
			hosts_arr =["%", "localhost"]
			for host in hosts_arr:
				get_cmd = self.get_jisql_cmd(root_user, db_root_password, 'mysql')
				if self.verify_user(root_user, db_root_password, host, db_user, get_cmd,dryMode):
					if dryMode == False:
						log("[I] MySQL user " + db_user + " already exists for host " + host, "info")
				else:
					if db_password == "":
						if dryMode == False:
							log("[I] MySQL user " + db_user + " does not exists for host " + host, "info")
							if os_name == "LINUX":
								query = get_cmd + " -query \"create user '%s'@'%s';\"" %(db_user, host)
								ret = subprocess.call(shlex.split(query))
							elif os_name == "WINDOWS":
								query = get_cmd + " -query \"create user '%s'@'%s';\" -c ;" %(db_user, host)
								ret = subprocess.call(query)
							if ret == 0:
								if self.verify_user(root_user, db_root_password, host, db_user, get_cmd,dryMode):
									log("[I] MySQL user " + db_user +" created for host " + host ,"info")
								else:
									log("[E] Creating MySQL user " + db_user +" failed..","error")
									sys.exit(1)
						else:
							logFile("create user '%s'@'%s';" %(db_user, host))
					else:
						if dryMode == False:
							log("[I] MySQL user " + db_user + " does not exists for host " + host, "info")
							if os_name == "LINUX":
								query = get_cmd + " -query \"create user '%s'@'%s' identified by '%s';\"" %(db_user, host, db_password)
								ret = subprocess.call(shlex.split(query))
							elif os_name == "WINDOWS":
								query = get_cmd + " -query \"create user '%s'@'%s' identified by '%s';\" -c ;" %(db_user, host, db_password)
								ret = subprocess.call(query)
							if ret == 0:
								if self.verify_user(root_user, db_root_password, host, db_user, get_cmd,dryMode):
									log("[I] MySQL user " + db_user +" created for host " + host ,"info")
								else:
									log("[E] Creating MySQL user " + db_user +" failed..","error")
									sys.exit(1)
							else:
								log("[E] Creating MySQL user " + db_user +" failed..","error")
								sys.exit(1)
						else:
							logFile("create user '%s'@'%s' identified by '%s';" %(db_user, host,db_password))


	def verify_db(self, root_user, db_root_password, db_name,dryMode):
		if dryMode == False:
			log("[I] Verifying database " + db_name , "info")
		get_cmd = self.get_jisql_cmd(root_user, db_root_password, 'mysql')
		if os_name == "LINUX":
			query = get_cmd + " -query \"show databases like '%s';\"" %(db_name)
		elif os_name == "WINDOWS":
			query = get_cmd + " -query \"show databases like '%s';\" -c ;" %(db_name)
		output = check_output(query)
		if output.strip(db_name + " |"):
			return True
		else:
			return False


	def create_db(self, root_user, db_root_password, db_name, db_user, db_password,dryMode):
		if self.verify_db(root_user, db_root_password, db_name,dryMode):
			if dryMode == False:
				log("[I] Database "+db_name + " already exists.","info")
		else:
			get_cmd = self.get_jisql_cmd(root_user, db_root_password, 'mysql')
			if os_name == "LINUX":
				query = get_cmd + " -query \"create database %s;\"" %(db_name)
			elif os_name == "WINDOWS":
				query = get_cmd + " -query \"create database %s;\" -c ;" %(db_name)
			if dryMode == False:
				log("[I] Database does not exist, Creating database " + db_name,"info")
				if os_name == "LINUX":
					ret = subprocess.call(shlex.split(query))
				elif os_name == "WINDOWS":
					ret = subprocess.call(query)
				if ret != 0:
					log("[E] Database creation failed..","error")
					sys.exit(1)
				else:
					if self.verify_db(root_user, db_root_password, db_name,dryMode):
						log("[I] Creating database " + db_name + " succeeded", "info")
						return True
					else:
						log("[E] Database creation failed..","error")
						sys.exit(1)
			else:
				logFile("create database %s;" %(db_name))


	def grant_xa_db_user(self, root_user, db_name, db_user, db_password, db_root_password, is_revoke,dryMode):
		hosts_arr =["%", "localhost"]
		'''
			if is_revoke:
				for host in hosts_arr:
					get_cmd = self.get_jisql_cmd(root_user, db_root_password, 'mysql')
					query = get_cmd + " -query \"REVOKE ALL PRIVILEGES,GRANT OPTION FROM '%s'@'%s';\"" %(db_user, host)
					ret = subprocess.call(shlex.split(query))
					if ret == 0:
						query = get_cmd + " -query \"FLUSH PRIVILEGES;\""
						ret = subprocess.call(shlex.split(query))
						if ret != 0:
							sys.exit(1)
					else:
						sys.exit(1)
		'''

		for host in hosts_arr:
			if dryMode == False:
				log("[I] ---------- Granting privileges TO user '"+db_user+"'@'"+host+"' on db '"+db_name+"'----------" , "info")
				get_cmd = self.get_jisql_cmd(root_user, db_root_password, 'mysql')
				if os_name == "LINUX":
					query = get_cmd + " -query \"grant all privileges on %s.* to '%s'@'%s' with grant option;\"" %(db_name,db_user, host)
					ret = subprocess.call(shlex.split(query))
				elif os_name == "WINDOWS":
					query = get_cmd + " -query \"grant all privileges on %s.* to '%s'@'%s' with grant option;\" -c ;" %(db_name,db_user, host)
					ret = subprocess.call(query)
				if ret == 0:
					log("[I] ---------- FLUSH PRIVILEGES ----------" , "info")
					if os_name == "LINUX":
						query = get_cmd + " -query \"FLUSH PRIVILEGES;\""
						ret = subprocess.call(shlex.split(query))
					elif os_name == "WINDOWS":
						query = get_cmd + " -query \"FLUSH PRIVILEGES;\" -c ;"
						ret = subprocess.call(query)
					if ret == 0:
						log("[I] Privileges granted to '" + db_user + "' on '"+db_name+"'", "info")
					else:
						log("[E] Granting privileges to '" +db_user+"' failed on '"+db_name+"'", "error")
						sys.exit(1)
				else:
					log("[E] Granting privileges to '" +db_user+"' failed on '"+db_name+"'", "error")
					sys.exit(1)
			else:
				logFile("grant all privileges on %s.* to '%s'@'%s' with grant option;" %(db_name,db_user, host))


class OracleConf(BaseDB):
	# Constructor
	def __init__(self, host, SQL_CONNECTOR_JAR, JAVA_BIN):
		self.host = host 
		self.SQL_CONNECTOR_JAR = SQL_CONNECTOR_JAR
		self.JAVA_BIN = JAVA_BIN

	def get_jisql_cmd(self, user, password):
		#TODO: User array for forming command
		path = os.getcwd()
		if os_name == "LINUX":
			jisql_cmd = "%s -cp %s:jisql/lib/* org.apache.util.sql.Jisql -driver oraclethin -cstring jdbc:oracle:thin:@%s -u '%s' -p '%s' -noheader -trim" %(self.JAVA_BIN, self.SQL_CONNECTOR_JAR, self.host, user, password)
		elif os_name == "WINDOWS":
			jisql_cmd = "%s -cp %s;%s\jisql\\lib\\* org.apache.util.sql.Jisql -driver oraclethin -cstring jdbc:oracle:thin:@%s -u %s -p %s -noheader -trim" %(self.JAVA_BIN, self.SQL_CONNECTOR_JAR, path, self.host, user, password)
		return jisql_cmd

	def check_connection(self, db_name, db_user, db_password):
		log("[I] Checking connection", "info")
		get_cmd = self.get_jisql_cmd(db_user, db_password)
		if os_name == "LINUX":
			query = get_cmd + " -c \; -query \"select * from v$version;\""
		elif os_name == "WINDOWS":
			query = get_cmd + " -query \"select * from v$version;\" -c ;"
		output = check_output(query)
		if output.strip('Production  |'):
			log("[I] Connection success", "info")
			return True
		else:
			log("[E] Can't establish connection,Change configuration or Contact Administrator!!", "error")
			sys.exit(1)

	def verify_user(self, root_user, db_user, db_root_password,dryMode):
		if dryMode == False:
			log("[I] Verifying user " + db_user ,"info")
		get_cmd = self.get_jisql_cmd(root_user, db_root_password)		
		if os_name == "LINUX":
			query = get_cmd + " -c \; -query \"select username from all_users where upper(username)=upper('%s');\"" %(db_user)
		elif os_name == "WINDOWS":
			query = get_cmd + " -query \"select username from all_users where upper(username)=upper('%s');\" -c ;" %(db_user)
		output = check_output(query)
		if output.strip(db_user + " |"):
			return True
		else:
			return False

	def create_rangerdb_user(self, root_user, db_user, db_password, db_root_password,dryMode):
		if self.check_connection(self, root_user, db_root_password):
			if self.verify_user(root_user, db_user, db_root_password,dryMode):
				if dryMode == False:
					log("[I] Oracle user " + db_user + " already exists.", "info")
			else:
				if dryMode == False:
					log("[I] User does not exists, Creating user : " + db_user, "info")
					get_cmd = self.get_jisql_cmd(root_user, db_root_password)
					if os_name == "LINUX":
						query = get_cmd + " -c \; -query 'create user %s identified by \"%s\";'" %(db_user, db_password)
						ret = subprocess.call(shlex.split(query))
					elif os_name == "WINDOWS":
						query = get_cmd + " -query \"create user %s identified by \"%s\";\" -c ;" %(db_user, db_password)
						ret = subprocess.call(query)
					if ret == 0:
						if self.verify_user(root_user, db_user, db_root_password,dryMode):
							log("[I] User " + db_user + " created", "info")
							log("[I] Granting permission to " + db_user, "info")
							if os_name == "LINUX":
								query = get_cmd + " -c \; -query 'GRANT CREATE SESSION,CREATE PROCEDURE,CREATE TABLE,CREATE VIEW,CREATE SEQUENCE,CREATE PUBLIC SYNONYM,CREATE TRIGGER,UNLIMITED Tablespace TO %s WITH ADMIN OPTION;'" % (db_user)
								ret = subprocess.call(shlex.split(query))
							elif os_name == "WINDOWS":
								query = get_cmd + " -query \"GRANT CREATE SESSION,CREATE PROCEDURE,CREATE TABLE,CREATE VIEW,CREATE SEQUENCE,CREATE PUBLIC SYNONYM,CREATE TRIGGER,UNLIMITED Tablespace TO %s WITH ADMIN OPTION;\" -c ;" % (db_user)
								ret = subprocess.call(query)
							if ret == 0:
								log("[I] Granting permissions to Oracle user '" + db_user + "' for %s done" %(self.host), "info")
							else:
								log("[E] Granting permissions to Oracle user '" + db_user + "' failed..", "error")
								sys.exit(1)
						else:
							log("[E] Creating Oracle user '" + db_user + "' failed..", "error")
							sys.exit(1)
					else:
						log("[E] Creating Oracle user '" + db_user + "' failed..", "error")
						sys.exit(1)
				else:
					logFile("create user %s identified by \"%s\";" %(db_user, db_password))


	def verify_tablespace(self, root_user, db_root_password, db_name,dryMode):
		if dryMode == False:
			log("[I] Verifying tablespace " + db_name, "info")
		get_cmd = self.get_jisql_cmd(root_user, db_root_password)		
		if os_name == "LINUX":
			query = get_cmd + " -c \; -query \"SELECT DISTINCT UPPER(TABLESPACE_NAME) FROM USER_TablespaceS where UPPER(Tablespace_Name)=UPPER(\'%s\');\"" %(db_name)
		elif os_name == "WINDOWS":
			query = get_cmd + " -query \"SELECT DISTINCT UPPER(TABLESPACE_NAME) FROM USER_TablespaceS where UPPER(Tablespace_Name)=UPPER(\'%s\');\" -c ;" %(db_name)
		output = check_output(query)
		if output.strip(db_name+' |'):
			return True
		else:
			return False

	def create_db(self, root_user, db_root_password, db_name, db_user, db_password,dryMode):
		if self.verify_tablespace(root_user, db_root_password, db_name,dryMode):
			if dryMode == False:
				log("[I] Tablespace " + db_name + " already exists.","info")
				if self.verify_user(root_user, db_user, db_root_password,dryMode):
					get_cmd = self.get_jisql_cmd(db_user ,db_password)
					if os_name == "LINUX":
						query = get_cmd + " -c \; -query 'select default_tablespace from user_users;'"
					elif os_name == "WINDOWS":
						query = get_cmd + " -query \"select default_tablespace from user_users;\" -c ;"
					output = check_output(query).strip()
					db_name = db_name.upper() +' |'
					if output == db_name:
						log("[I] User name " + db_user + " and tablespace " + db_name + " already exists.","info")
					else:
						log("[E] "+db_user + " user already assigned some other tablespace , give some other DB name.","error")
						sys.exit(1)
					#status = self.assign_tablespace(root_user, db_root_password, db_user, db_password, db_name, False)
					#return status
		else:
			if dryMode == False:
				log("[I] Tablespace does not exist. Creating tablespace: " + db_name,"info")
				get_cmd = self.get_jisql_cmd(root_user, db_root_password)
				if os_name == "LINUX":
					query = get_cmd + " -c \; -query \"create tablespace %s datafile '%s.dat' size 10M autoextend on;\"" %(db_name, db_name)
					ret = subprocess.call(shlex.split(query))
				elif os_name == "WINDOWS":
					query = get_cmd + " -query \"create tablespace %s datafile '%s.dat' size 10M autoextend on;\" -c ;" %(db_name, db_name)
					ret = subprocess.call(query)
				if ret == 0:
					if self.verify_tablespace(root_user, db_root_password, db_name,dryMode):
						log("[I] Creating tablespace "+db_name+" succeeded", "info")
						status=True
						status = self.assign_tablespace(root_user, db_root_password, db_user, db_password, db_name, status,dryMode)
						return status
					else:
						log("[E] Creating tablespace "+db_name+" failed..", "error")
						sys.exit(1)
				else:
					log("[E] Creating tablespace "+db_name+" failed..", "error")
					sys.exit(1)
			else:
				logFile("create tablespace %s datafile '%s.dat' size 10M autoextend on;" %(db_name, db_name))

	def assign_tablespace(self, root_user, db_root_password, db_user, db_password, db_name, status,dryMode):
		if dryMode == False:
			log("[I] Assign default tablespace " +db_name + " to " + db_user, "info")
			# Assign default tablespace db_name
			get_cmd = self.get_jisql_cmd(root_user , db_root_password)
			if os_name == "LINUX":
				query = get_cmd +" -c \; -query 'alter user %s identified by \"%s\" DEFAULT Tablespace %s;'" %(db_user, db_password, db_name)
				ret = subprocess.call(shlex.split(query))
			elif os_name == "WINDOWS":
				query = get_cmd +" -query \"alter user %s identified by \"%s\" DEFAULT Tablespace %s;\" -c ;" %(db_user, db_password, db_name)
				ret = subprocess.call(query)
			if ret == 0:
				log("[I] Granting permission to " + db_user, "info")
				if os_name == "LINUX":
					query = get_cmd + " -c \; -query 'GRANT CREATE SESSION,CREATE PROCEDURE,CREATE TABLE,CREATE VIEW,CREATE SEQUENCE,CREATE PUBLIC SYNONYM,CREATE TRIGGER,UNLIMITED Tablespace TO %s WITH ADMIN OPTION;'" % (db_user)
					ret = subprocess.call(shlex.split(query))
				elif os_name == "WINDOWS":
					query = get_cmd + " -query \"GRANT CREATE SESSION,CREATE PROCEDURE,CREATE TABLE,CREATE VIEW,CREATE SEQUENCE,CREATE PUBLIC SYNONYM,CREATE TRIGGER,UNLIMITED Tablespace TO %s WITH ADMIN OPTION;\" -c ;" % (db_user)
					ret = subprocess.call(query)
				if ret == 0:
					log("[I] Granting Oracle user '" + db_user + "' done", "info")
					return status
				else:
					log("[E] Granting Oracle user '" + db_user + "' failed..", "error")
					sys.exit(1)
			else:
				log("[E] Assigning default tablespace to user '" + db_user + "' failed..", "error")
				sys.exit(1)
		else:
			logFile("alter user %s identified by \"%s\" DEFAULT Tablespace %s;" %(db_user, db_password, db_name))
			logFile("GRANT CREATE SESSION,CREATE PROCEDURE,CREATE TABLE,CREATE VIEW,CREATE SEQUENCE,CREATE PUBLIC SYNONYM,CREATE TRIGGER,UNLIMITED Tablespace TO %s WITH ADMIN OPTION;" % (db_user))


	def grant_xa_db_user(self, root_user, db_name, db_user, db_password, db_root_password, invoke,dryMode):
		if dryMode == False:
			get_cmd = self.get_jisql_cmd(root_user ,db_root_password)
			if os_name == "LINUX":
				query = get_cmd + " -c \; -query 'GRANT CREATE SESSION,CREATE PROCEDURE,CREATE TABLE,CREATE VIEW,CREATE SEQUENCE,CREATE PUBLIC SYNONYM,CREATE TRIGGER,UNLIMITED Tablespace TO %s WITH ADMIN OPTION;'" % (db_user)
				ret = subprocess.call(shlex.split(query))
			elif os_name == "WINDOWS":
				query = get_cmd + " -query \"GRANT CREATE SESSION,CREATE PROCEDURE,CREATE TABLE,CREATE VIEW,CREATE SEQUENCE,CREATE PUBLIC SYNONYM,CREATE TRIGGER,UNLIMITED Tablespace TO %s WITH ADMIN OPTION;\" -c ;" % (db_user)
				ret = subprocess.call(query)
			if ret == 0:
				log("[I] Granted permission to " + db_user, "info")
				return True
			else:
				log("[E] Granting Oracle user '" + db_user + "' failed..", "error")
				sys.exit(1)
		else:
			logFile("GRANT CREATE SESSION,CREATE PROCEDURE,CREATE TABLE,CREATE VIEW,CREATE SEQUENCE,CREATE PUBLIC SYNONYM,CREATE TRIGGER,UNLIMITED Tablespace TO %s WITH ADMIN OPTION;" % (db_user))



class PostgresConf(BaseDB):
	# Constructor
	def __init__(self, host, SQL_CONNECTOR_JAR, JAVA_BIN):
		self.host = host
		self.SQL_CONNECTOR_JAR = SQL_CONNECTOR_JAR
		self.JAVA_BIN = JAVA_BIN

	def get_jisql_cmd(self, user, password, db_name):
		#TODO: User array for forming command
		path = os.getcwd()
		self.JAVA_BIN = self.JAVA_BIN.strip("'")
		if os_name == "LINUX":
			jisql_cmd = "%s -cp %s:jisql/lib/* org.apache.util.sql.Jisql -driver postgresql -cstring jdbc:postgresql://%s:5432/%s -u %s -p %s -noheader -trim -c \;" %(self.JAVA_BIN, self.SQL_CONNECTOR_JAR, self.host, db_name, user, password)
		elif os_name == "WINDOWS":
			jisql_cmd = "%s -cp %s;%s\jisql\\lib\\* org.apache.util.sql.Jisql -driver postgresql -cstring jdbc:postgresql://%s:5432/%s -u %s -p %s -noheader -trim" %(self.JAVA_BIN, self.SQL_CONNECTOR_JAR, path, self.host, db_name, user, password)
		return jisql_cmd

	def verify_user(self, root_user, db_root_password, db_user,dryMode):
		if dryMode == False:
			log("[I] Verifying user " + db_user , "info")
		get_cmd = self.get_jisql_cmd(root_user, db_root_password, 'postgres')
		if os_name == "LINUX":
			query = get_cmd + " -query \"SELECT rolname FROM pg_roles WHERE rolname='%s';\"" %(db_user)
		elif os_name == "WINDOWS":
			query = get_cmd + " -query \"SELECT rolname FROM pg_roles WHERE rolname='%s';\" -c ;" %(db_user)
		output = check_output(query)
		if output.strip(db_user + " |"):
			return True
		else:
			return False

	def check_connection(self, db_name, db_user, db_password):
		#log("[I] Checking connection", "info")
		get_cmd = self.get_jisql_cmd(db_user, db_password, db_name)
		if os_name == "LINUX":
			query = get_cmd + " -query \"SELECT 1;\""
		elif os_name == "WINDOWS":
			query = get_cmd + " -query \"SELECT 1;\" -c ;"
		output = check_output(query)
		if output.strip('1 |'):
			#log("[I] connection success", "info")
			return True
		else:
			log("[E] Can't establish connection, Please check connection settings or contact Administrator", "error")
			sys.exit(1)

	def create_rangerdb_user(self, root_user, db_user, db_password, db_root_password,dryMode):
		if self.check_connection('postgres', root_user, db_root_password):
			if self.verify_user(root_user, db_root_password, db_user,dryMode):
				if dryMode == False:
					log("[I] Postgres user " + db_user + " already exists.", "info")
			else:
				if dryMode == False:
					log("[I] User does not exists, Creating user : " + db_user, "info")
					get_cmd = self.get_jisql_cmd(root_user, db_root_password, 'postgres')
					if os_name == "LINUX":
						query = get_cmd + " -query \"CREATE USER %s WITH LOGIN PASSWORD '%s';\"" %(db_user, db_password)
						ret = subprocess.call(shlex.split(query))
					elif os_name == "WINDOWS":
						query = get_cmd + " -query \"CREATE USER %s WITH LOGIN PASSWORD '%s';\" -c ;" %(db_user, db_password)
						ret = subprocess.call(query)
					if ret == 0:
						if self.verify_user(root_user, db_root_password, db_user,dryMode):
							log("[I] Postgres user " + db_user + " created", "info")
						else:
							log("[E] Postgres user " +db_user+" creation failed..", "error")
							sys.exit(1)
					else:
						log("[E] Postgres user " +db_user+" creation failed..", "error")
						sys.exit(1)
				else:
					logFile("CREATE USER %s WITH LOGIN PASSWORD '%s';" %(db_user, db_password))

	def verify_db(self, root_user, db_root_password, db_name,dryMode):
		if dryMode == False:
			log("[I] Verifying database " + db_name , "info")
		get_cmd = self.get_jisql_cmd(root_user, db_root_password, 'postgres')
		if os_name == "LINUX":
			query = get_cmd + " -query \"SELECT datname FROM pg_database where datname='%s';\"" %(db_name)
		elif os_name == "WINDOWS":
			query = get_cmd + " -query \"SELECT datname FROM pg_database where datname='%s';\" -c ;" %(db_name)
		output = check_output(query)
		if output.strip(db_name + " |"):
			return True
		else:
			return False


	def create_db(self, root_user, db_root_password, db_name, db_user, db_password,dryMode):
		if self.verify_db(root_user, db_root_password, db_name,dryMode):
			if dryMode == False:
				log("[I] Database "+db_name + " already exists.", "info")
		else:
			if dryMode == False:
				log("[I] Database does not exist, Creating database : " + db_name,"info")
				get_cmd = self.get_jisql_cmd(root_user, db_root_password, 'postgres')
				if os_name == "LINUX":
					query = get_cmd + " -query \"create database %s with OWNER %s;\"" %(db_name, db_user)
					ret = subprocess.call(shlex.split(query))
				elif os_name == "WINDOWS":
					query = get_cmd + " -query \"create database %s with OWNER %s;\" -c ;" %(db_name, db_user)
					ret = subprocess.call(query)
				if ret != 0:
					log("[E] Database creation failed..","error")
					sys.exit(1)
				else:
					if self.verify_db(root_user, db_root_password, db_name,dryMode):
						log("[I] Creating database " + db_name + " succeeded", "info")
						return True
					else:
						log("[E] Database creation failed..","error")
						sys.exit(1)
			else:
				logFile("CREATE DATABASE %s WITH OWNER %s;" %(db_name, db_user))

	def grant_xa_db_user(self, root_user, db_name, db_user, db_password, db_root_password , is_revoke,dryMode):
		if dryMode == False:
			log("[I] Granting privileges TO user '"+db_user+"' on db '"+db_name+"'" , "info")
			get_cmd = self.get_jisql_cmd(root_user, db_root_password, db_name)
			if os_name == "LINUX":
				query = get_cmd + " -query \"GRANT ALL PRIVILEGES ON DATABASE %s to %s;\"" %(db_name, db_user)
				ret = subprocess.call(shlex.split(query))
			elif os_name == "WINDOWS":
				query = get_cmd + " -query \"GRANT ALL PRIVILEGES ON DATABASE %s to %s;\" -c ;" %(db_name, db_user)
				ret = subprocess.call(query)
			if ret != 0:
				log("[E] Granting all privileges on database "+db_name+" to user "+db_user+" failed..", "error")
				sys.exit(1)

			if os_name == "LINUX":
				query = get_cmd + " -query \"GRANT ALL PRIVILEGES ON SCHEMA public TO %s;\"" %(db_user)
				ret = subprocess.call(shlex.split(query))
			elif os_name == "WINDOWS":
				query = get_cmd + " -query \"GRANT ALL PRIVILEGES ON SCHEMA public TO %s;\" -c ;" %(db_user)
				ret = subprocess.call(query)
			if ret != 0:
				log("[E] Granting all privileges on schema public to user "+db_user+" failed..", "error")
				sys.exit(1)

			if os_name == "LINUX":
				query = get_cmd + " -query \"SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';\""
				output = check_output(query)
			elif os_name == "WINDOWS":
				query = get_cmd + " -query \"SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';\" -c ;"
				output = check_output(query)
			for each_line in output.split('\n'):
				if len(each_line) == 0 : continue
				if re.search(' |', each_line):
					tablename , value = each_line.strip().split(" |",1)
					tablename = tablename.strip()
					if os_name == "LINUX":
						query1 = get_cmd + " -query \"GRANT ALL PRIVILEGES ON TABLE %s TO %s;\"" %(tablename,db_user)
						ret = subprocess.call(shlex.split(query1))
						if ret != 0:
							log("[E] Granting all privileges on tablename "+tablename+" to user "+db_user+" failed..", "error")
							sys.exit(1)
					elif os_name == "WINDOWS":
						query1 = get_cmd + " -query \"GRANT ALL PRIVILEGES ON TABLE %s TO %s;\" -c ;" %(tablename,db_user)
						ret = subprocess.call(query1)
						if ret != 0:
							log("[E] Granting all privileges on tablename "+tablename+" to user "+db_user+" failed..", "error")
							sys.exit(1)


			if os_name == "LINUX":
				query = get_cmd + " -query \"SELECT sequence_name FROM information_schema.sequences where sequence_schema='public';\""
				output = check_output(query)
			elif os_name == "WINDOWS":
				query = get_cmd + " -query \"SELECT sequence_name FROM information_schema.sequences where sequence_schema='public';\" -c ;"
				output = check_output(query)
			for each_line in output.split('\n'):
				if len(each_line) == 0 : continue
				if re.search(' |', each_line):
					sequence_name , value = each_line.strip().split(" |",1)
					sequence_name = sequence_name.strip()
					if os_name == "LINUX":
						query1 = get_cmd + " -query \"GRANT ALL PRIVILEGES ON SEQUENCE %s TO %s;\"" %(sequence_name,db_user)
						ret = subprocess.call(shlex.split(query1))
						if ret != 0:
							log("[E] Granting all privileges on sequence "+sequence_name+" to user "+db_user+" failed..", "error")
							sys.exit(1)
					elif os_name == "WINDOWS":
						query1 = get_cmd + " -query \"GRANT ALL PRIVILEGES ON SEQUENCE %s TO %s;\" -c ;" %(sequence_name,db_user)
						ret = subprocess.call(query1)
						if ret != 0:
							log("[E] Granting all privileges on sequence "+sequence_name+" to user "+db_user+" failed..", "error")
							sys.exit(1)

			log("[I] Granting privileges TO user '"+db_user+"' on db '"+db_name+"' Done" , "info")
		else:
			logFile("GRANT ALL PRIVILEGES ON DATABASE %s to %s;" %(db_name, db_user))
			logFile("GRANT ALL PRIVILEGES ON SCHEMA public TO %s;" %( db_user))
			logFile("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO %s;" %(db_user))
			logFile("GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO %s;" %(db_user))



class SqlServerConf(BaseDB):
	# Constructor
	def __init__(self, host, SQL_CONNECTOR_JAR, JAVA_BIN):
		self.host = host
		self.SQL_CONNECTOR_JAR = SQL_CONNECTOR_JAR
		self.JAVA_BIN = JAVA_BIN

	def get_jisql_cmd(self, user, password, db_name):
		#TODO: User array for forming command
		path = os.getcwd()
		self.JAVA_BIN = self.JAVA_BIN.strip("'")
		if os_name == "LINUX":
			jisql_cmd = "%s -cp %s:jisql/lib/* org.apache.util.sql.Jisql -user %s -password %s -driver mssql -cstring jdbc:sqlserver://%s:1433\\;databaseName=%s -noheader -trim"%(self.JAVA_BIN, self.SQL_CONNECTOR_JAR, user, password, self.host,db_name)
		elif os_name == "WINDOWS":
			jisql_cmd = "%s -cp %s;%s\\jisql\\lib\\* org.apache.util.sql.Jisql -user %s -password %s -driver mssql -cstring jdbc:sqlserver://%s:1433;databaseName=%s -noheader -trim"%(self.JAVA_BIN, self.SQL_CONNECTOR_JAR, path, user, password, self.host,db_name)
		return jisql_cmd

	def verify_user(self, root_user, db_root_password, db_user,dryMode):
		if dryMode == False:
			log("[I] Verifying user " + db_user , "info")
		get_cmd = self.get_jisql_cmd(root_user, db_root_password, 'msdb')
		if os_name == "LINUX":
			query = get_cmd + " -c \; -query \"select loginname from master.dbo.syslogins where loginname = '%s';\"" %(db_user)
		elif os_name == "WINDOWS":
			query = get_cmd + " -query \"select loginname from master.dbo.syslogins where loginname = '%s';\" -c ;" %(db_user)
		output = check_output(query)
		if output.strip(db_user + " |"):
			return True
		else:
			return False

	def check_connection(self, db_name, db_user, db_password):
		log("[I] Checking connection", "info")
		get_cmd = self.get_jisql_cmd(db_user, db_password, db_name)
		if os_name == "LINUX":
			query = get_cmd + " -c \; -query \"SELECT 1;\""
		elif os_name == "WINDOWS":
			query = get_cmd + " -query \"SELECT 1;\" -c ;"
		output = check_output(query)
		if output.strip('1 |'):
			log("[I] Connection success", "info")
			return True
		else:
			log("[E] Can't establish connection", "error")
			sys.exit(1)

	def create_rangerdb_user(self, root_user, db_user, db_password, db_root_password,dryMode):
		if self.check_connection('msdb', root_user, db_root_password):
			if self.verify_user(root_user, db_root_password, db_user,dryMode):
				if dryMode == False:
					log("[I] SQL Server user " + db_user + " already exists.", "info")
			else:
				if dryMode == False:
					get_cmd = self.get_jisql_cmd(root_user, db_root_password, 'msdb')
					log("[I] User does not exists, Creating Login user " + db_user, "info")
					if os_name == "LINUX":
						query = get_cmd + " -c \; -query \"CREATE LOGIN %s WITH PASSWORD = '%s';\"" %(db_user,db_password)
						ret = subprocess.call(shlex.split(query))
					elif os_name == "WINDOWS":
						query = get_cmd + " -query \"CREATE LOGIN %s WITH PASSWORD = '%s';\" -c ;" %(db_user,db_password)
						ret = subprocess.call(query)
					if ret == 0:
						if self.verify_user(root_user, db_root_password, db_user,dryMode):
							 log("[I] SQL Server user " + db_user + " created", "info")
						else:
							log("[E] SQL Server user " +db_user+" creation failed..", "error")
							sys.exit(1)
					else:
						log("[E] SQL Server user " +db_user+" creation failed..", "error")
						sys.exit(1)
				else:
					logFile("CREATE LOGIN %s WITH PASSWORD = '%s';" %(db_user,db_password))

	def verify_db(self, root_user, db_root_password, db_name,dryMode):
		if dryMode == False:
			log("[I] Verifying database " + db_name, "info")
		get_cmd = self.get_jisql_cmd(root_user, db_root_password, 'msdb')
		if os_name == "LINUX":
			query = get_cmd + " -c \; -query \"SELECT name from sys.databases where name='%s';\"" %(db_name)
		elif os_name == "WINDOWS":
			query = get_cmd + " -query \"SELECT name from sys.databases where name='%s';\" -c ;" %(db_name)
		output = check_output(query)
		if output.strip(db_name + " |"):
			return True
		else:
			return False

	def create_db(self, root_user, db_root_password, db_name, db_user, db_password,dryMode):
		if self.verify_db(root_user, db_root_password, db_name,dryMode):
			if dryMode == False:
				log("[I] Database " + db_name + " already exists.","info")
		else:
			if dryMode == False:
				log("[I] Database does not exist. Creating database : " + db_name,"info")
				get_cmd = self.get_jisql_cmd(root_user, db_root_password, 'msdb')
				if os_name == "LINUX":
					query = get_cmd + " -c \; -query \"create database %s;\"" %(db_name)
					ret = subprocess.call(shlex.split(query))
				elif os_name == "WINDOWS":
					query = get_cmd + " -query \"create database %s;\" -c ;" %(db_name)
					ret = subprocess.call(query)
				if ret != 0:
					log("[E] Database creation failed..","error")
					sys.exit(1)
				else:
					if self.verify_db(root_user, db_root_password, db_name,dryMode):
						self.create_user(root_user, db_name ,db_user, db_password, db_root_password,dryMode)
						log("[I] Creating database " + db_name + " succeeded", "info")
						return True
	#	        	               	self.import_db_file(db_name, root_user, db_user, db_password, db_root_password, file_name)
					else:
						log("[E] Database creation failed..","error")
						sys.exit(1)
			else:
				logFile("create database %s;" %(db_name))

	def create_user(self, root_user, db_name ,db_user, db_password, db_root_password,dryMode):
		get_cmd = self.get_jisql_cmd(root_user, db_root_password, 'msdb')
		if os_name == "LINUX":
			query = get_cmd + " -c \; -query \"USE %s SELECT name FROM sys.database_principals WHERE name = N'%s';\"" %(db_name, db_user)
		elif os_name == "WINDOWS":
			query = get_cmd + " -query \"USE %s SELECT name FROM sys.database_principals WHERE name = N'%s';\" -c ;" %(db_name, db_user)
		output = check_output(query)
		if output.strip(db_user + " |"):
			if dryMode == False:
				log("[I] User "+db_user+" exist ","info")
		else:
			if dryMode == False:
				if os_name == "LINUX":
					query = get_cmd + " -c \; -query \"USE %s CREATE USER %s for LOGIN %s;\"" %(db_name ,db_user, db_user)
					ret = subprocess.call(shlex.split(query))
				elif os_name == "WINDOWS":
					query = get_cmd + " -query \"USE %s CREATE USER %s for LOGIN %s;\" -c ;" %(db_name ,db_user, db_user)
					ret = subprocess.call(query)
				if ret == 0:
					if os_name == "LINUX":
						query = get_cmd + " -c \; -query \"USE %s SELECT name FROM sys.database_principals WHERE name = N'%s';\"" %(db_name ,db_user)
					elif os_name == "WINDOWS":
						query = get_cmd + " -query \"USE %s SELECT name FROM sys.database_principals WHERE name = N'%s';\" -c ;" %(db_name ,db_user)
					output = check_output(query)
					if output.strip(db_user + " |"):
						log("[I] User "+db_user+" exist ","info")
					else:
						log("[E] Database creation failed..","error")
						sys.exit(1)
				else:
					log("[E] Database creation failed..","error")
					sys.exit(1)
			else:
				logFile("USE %s CREATE USER %s for LOGIN %s;" %(db_name ,db_user, db_user))

	def grant_xa_db_user(self, root_user, db_name, db_user, db_password, db_root_password, is_revoke,dryMode):
		if dryMode == False:
			log("[I] Granting permission to admin user '" + db_user + "' on db '" + db_name + "'" , "info")
			get_cmd = self.get_jisql_cmd(root_user, db_root_password, 'msdb')
			if os_name == "LINUX":
				query = get_cmd + " -c \; -query \"ALTER LOGIN [%s] WITH DEFAULT_DATABASE=[%s];\"" %(db_user, db_name)
				ret = subprocess.call(shlex.split(query))
			elif os_name == "WINDOWS":
				query = get_cmd + " -query \"ALTER LOGIN [%s] WITH DEFAULT_DATABASE=[%s];\" -c ;" %(db_user, db_name)
				ret = subprocess.call(query)
			if ret != 0:
				sys.exit(1)
			if os_name == "LINUX":
				query = get_cmd + " -c \; -query \" USE %s EXEC sp_addrolemember N'db_owner', N'%s';\"" %(db_name, db_user)
#           	     query = get_cmd + " -c \; -query \" USE %s GRANT ALL PRIVILEGES to %s;\"" %(db_name , db_user)
				ret = subprocess.call(shlex.split(query))
			elif os_name == "WINDOWS":
				query = get_cmd + " -query \" USE %s EXEC sp_addrolemember N'db_owner', N'%s';\" -c ;" %(db_name, db_user)
#           	     query = get_cmd + " -c \; -query \" USE %s GRANT ALL PRIVILEGES to %s;\"" %(db_name , db_user)
				ret = subprocess.call(query)
			if ret != 0:
				sys.exit(1)
		else:
			logFile("ALTER LOGIN [%s] WITH DEFAULT_DATABASE=[%s];" %(db_user, db_name))
			logFile("USE %s EXEC sp_addrolemember N'db_owner', N'%s';" %(db_name, db_user))


def main(argv):

	FORMAT = '%(asctime)-15s %(message)s'
	logging.basicConfig(format=FORMAT, level=logging.DEBUG)
	DBA_MODE = 'TRUE'

	quiteMode = False
	dryMode=False
	is_revoke=False

	if len(argv) > 1:
		for i in range(len(argv)):
			if str(argv[i]) == "-q":
				quiteMode = True
				populate_global_dict()
			if str(argv[i]) == "-d":
				index=i+1
				try:
					dba_sql_file=str(argv[index])
					if dba_sql_file == "":
						log("[E] Invalid input! Provide file path to write DBA scripts:","error")
						sys.exit(1)
				except IndexError:
					log("[E] Invalid input! Provide file path to write DBA scripts:","error")
					sys.exit(1)

				if not dba_sql_file == "":
					if not os.path.exists(dba_sql_file):
						log("[I] Creating File:"+dba_sql_file,"info")
						open(dba_sql_file, 'w').close()
					else:
						log("[I] File "+dba_sql_file+ " is available.","info")

					if os.path.isfile(dba_sql_file):
						dryMode=True
						globalDict["dryMode"]=True
						globalDict["dryModeOutputFile"]=dba_sql_file
					else:
						log("[E] Invalid file Name! Unable to find file:"+dba_sql_file,"error")
						sys.exit(1)

	log("[I] Running DBA setup script. QuiteMode:" + str(quiteMode),"info")
	if (quiteMode):
		if os.environ['JAVA_HOME'] == "":
			log("[E] ---------- JAVA_HOME environment property not defined, aborting installation. ----------", "error")
			sys.exit(1)
		else:
			JAVA_BIN=os.path.join(os.environ['JAVA_HOME'],'bin','java')
		if os_name == "WINDOWS" :
			JAVA_BIN = JAVA_BIN+'.exe'
		if os.path.isfile(JAVA_BIN):
			pass
		else:
			JAVA_BIN=globalDict['JAVA_BIN']
			if os.path.isfile(JAVA_BIN):
				pass
			else:
				log("[E] ---------- JAVA Not Found, aborting installation. ----------", "error")
				sys.exit(1)
	else:
		if os.environ['JAVA_HOME'] == "":
			log("[E] ---------- JAVA_HOME environment property not defined, aborting installation. ----------", "error")
			sys.exit(1)
		JAVA_BIN=os.path.join(os.environ['JAVA_HOME'],'bin','java')
		if os_name == "WINDOWS" :
			JAVA_BIN = JAVA_BIN+'.exe'
		if os.path.isfile(JAVA_BIN):
			pass
		else :
			while os.path.isfile(JAVA_BIN) == False:
				log("Enter java executable path: :","info")
				JAVA_BIN=raw_input()
	log("[I] Using Java:" + str(JAVA_BIN),"info")

	if (quiteMode):
		XA_DB_FLAVOR=globalDict['DB_FLAVOR']
	else:
		XA_DB_FLAVOR=''
		while XA_DB_FLAVOR == "":
			log("Enter db flavour{MYSQL|ORACLE|POSTGRES|SQLSERVER} :","info")
			XA_DB_FLAVOR=raw_input()

	XA_DB_FLAVOR = XA_DB_FLAVOR.upper()
	log("[I] DB FLAVOR:" + str(XA_DB_FLAVOR),"info")

	if (quiteMode):
		CONNECTOR_JAR=globalDict['SQL_CONNECTOR_JAR']
	else:
		if XA_DB_FLAVOR == "MYSQL" or XA_DB_FLAVOR == "ORACLE" or XA_DB_FLAVOR == "POSTGRES" or XA_DB_FLAVOR == "SQLSERVER":
			log("Enter JDBC connector file for :"+XA_DB_FLAVOR,"info")
			CONNECTOR_JAR=raw_input()
			while os.path.isfile(CONNECTOR_JAR) == False:
				log("JDBC connector file "+CONNECTOR_JAR+" does not exist, Please enter connector path :","error")
				CONNECTOR_JAR=raw_input()
		else:
			log("[E] ---------- NO SUCH SUPPORTED DB FLAVOUR.. ----------", "error")
			sys.exit(1)

	if (quiteMode):
		xa_db_host = globalDict['db_host']
	else:
		xa_db_host=''
		while xa_db_host == "":
			log("Enter DB Host :","info")
			xa_db_host=raw_input()
	log("[I] DB Host:" + str(xa_db_host),"info")

	if (quiteMode):
		xa_db_root_user = globalDict['db_root_user']
		xa_db_root_password = globalDict['db_root_password']
	else:
		xa_db_root_user=''
		while xa_db_root_user == "":
			log("Enter db root user:","info")
			xa_db_root_user=raw_input()
			log("Enter db root password:","info")
			xa_db_root_password = getpass.getpass("Enter db root password:")

	if (quiteMode):
		db_name = globalDict['db_name']
	else:
		db_name = ''
		while db_name == "":
			log("Enter DB Name :","info")
			db_name=raw_input()

	if (quiteMode):
		db_user = globalDict['db_user']
	else:
		db_user=''
		while db_user == "":
			log("Enter db user name:","info")
			db_user=raw_input()

	if (quiteMode):
		db_password = globalDict['db_password']
	else:
		db_password=''
		while db_password == "":
			log("Enter db user password:","info")
			db_password = getpass.getpass("Enter db user password:")

	#mysql_core_file = globalDict['mysql_core_file']
	mysql_core_file = os.path.join('db','mysql','xa_core_db.sql')

	#oracle_core_file = globalDict['oracle_core_file'] 
	oracle_core_file = os.path.join('db','oracle','xa_core_db_oracle.sql')

	#postgres_core_file = globalDict['postgres_core_file']
	postgres_core_file = os.path.join('db','postgres','xa_core_db_postgres.sql')

	#sqlserver_core_file = globalDict['sqlserver_core_file']
	sqlserver_core_file = os.path.join('db','sqlserver','xa_core_db_sqlserver.sql')

	x_db_version = 'x_db_version_h'
	x_user = 'x_portal_user'

	if XA_DB_FLAVOR == "MYSQL":
		MYSQL_CONNECTOR_JAR=CONNECTOR_JAR
		xa_sqlObj = MysqlConf(xa_db_host, MYSQL_CONNECTOR_JAR, JAVA_BIN)
		xa_db_core_file = os.path.join(os.getcwd(),mysql_core_file)

	elif XA_DB_FLAVOR == "ORACLE":
		ORACLE_CONNECTOR_JAR=CONNECTOR_JAR
		if os_name == "LINUX":
			xa_db_root_user = xa_db_root_user+" AS SYSDBA"
		elif os_name == "WINDOWS":
			xa_db_root_user = xa_db_root_user
		xa_sqlObj = OracleConf(xa_db_host, ORACLE_CONNECTOR_JAR, JAVA_BIN)
		xa_db_core_file = os.path.join(os.getcwd(),oracle_core_file)

	elif XA_DB_FLAVOR == "POSTGRES":
		POSTGRES_CONNECTOR_JAR=CONNECTOR_JAR
		xa_sqlObj = PostgresConf(xa_db_host, POSTGRES_CONNECTOR_JAR, JAVA_BIN)
		xa_db_core_file = os.path.join(os.getcwd(),postgres_core_file)

	elif XA_DB_FLAVOR == "SQLSERVER":
		SQLSERVER_CONNECTOR_JAR=CONNECTOR_JAR
		xa_sqlObj = SqlServerConf(xa_db_host, SQLSERVER_CONNECTOR_JAR, JAVA_BIN)
		xa_db_core_file = os.path.join(os.getcwd(),sqlserver_core_file)
	else:
		log("[E] ---------- NO SUCH SUPPORTED DB FLAVOUR.. ----------", "error")
		sys.exit(1)


	# Methods Begin
	if DBA_MODE == "TRUE" :
		if (dryMode==True):
			log("[I] Dry run mode:"+str(dryMode),"info")
			log("[I] Logging DBA Script in file:"+str(globalDict["dryModeOutputFile"]),"info")
			logFile("===============================================\n")
			xa_sqlObj.create_rangerdb_user(xa_db_root_user, db_user, db_password, xa_db_root_password,dryMode)
			xa_sqlObj.create_db(xa_db_root_user, xa_db_root_password, db_name, db_user, db_password,dryMode)
			xa_sqlObj.grant_xa_db_user(xa_db_root_user, db_name, db_user, db_password, xa_db_root_password, is_revoke,dryMode)
			logFile("===============================================\n")
		if (dryMode==False):
			log("[I] ---------- Creating Ranger KMS db user ---------- ","info")
			xa_sqlObj.create_rangerdb_user(xa_db_root_user, db_user, db_password, xa_db_root_password,dryMode)
			log("[I] ---------- Creating Ranger KMS database ----------","info")
			xa_sqlObj.create_db(xa_db_root_user, xa_db_root_password, db_name, db_user, db_password,dryMode)
			log("[I] ---------- Granting permission to Ranger KMS db user ----------","info")
			xa_sqlObj.grant_xa_db_user(xa_db_root_user, db_name, db_user, db_password, xa_db_root_password, is_revoke,dryMode)
			# Ranger KMS DB Host AND Ranger Audit DB Host are Different OR Same
			log("[I] ---------- Ranger KMS DB and User Creation Process Completed..  ---------- ","info")
main(sys.argv)
