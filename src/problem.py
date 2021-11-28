#!/usr/bin/env python3

def verdict(data, ver):  # Save verdict and send back result to the client
    os.system('rm -rf ~/tmp')  # Clean up ~/tmp

    logging.info(ver)

    num = int(cur.execute('SELECT Count(*) FROM ' +
                          data['contest']+'_submissions').fetchone()[0])
    cur.execute('INSERT INTO '+data['contest']+'_submissions VALUES (?, ?, ?, ?, ?)',
                (num, data['username'], data['problem'], data['code'], ver))

    if cur.execute('SELECT Count(*) FROM '+data['contest']+'_status WHERE username = ?', (data['username'],)).fetchone()[0] == 0:
        command = 'INSERT INTO '+data['contest'] + \
            '_status VALUES ("'+data['username']+'", '
        for problem in os.listdir(cwd+data['contest']):
            if os.path.isfile(cwd+contest+'/'+problem) or problem.startswith('.'):
                continue
            command += '0, '
        command = command[:-2]+')'
        cur.execute(command)
    cur.execute('UPDATE '+data['contest']+'_status SET P'+data['problem'] +
                ' = ? WHERE username = ?', (str(ver), data['username'],))
    cur.commit()
    return ver


def submit(data):  # Process a submission
    if not user.authenticate(data) \
            or data['contest'] not in os.listdir('contests') or not os.path.exists(cwd+data['contest']+'/'+data['problem']) \
            or datetime.datetime.now() < datetime.datetime.fromisoformat(json.loads(open(cwd+data['contest']+'/info.json', 'r').read())['start-time']):
        return 404

    # Save the program
    os.system('mkdir ~/tmp -p')
    with open(os.path.expanduser('~/tmp/main.'+languages[data['language']].extension), 'w') as f:
        f.write(data['code'])
    # Sandboxing program
    if args.sandbox == 'firejail':
        sandbox = 'firejail --profile=firejail.profile bash -c '
    else:
        sandbox = 'bash -c '  # Dummy sandbox

    # Compile the code if needed
    if languages[data['language']].compile_cmd != '':
        ret = os.system('cd ~/tmp && timeout 10 ' +
                        languages[data['language']].compile_cmd)
        if ret:
            verdict(data, 500)
            return

    tcdir = cwd+data['contest']+'/'+problem+'/'
    with open(tcdir+'config.json') as f:
        config = json.loads(f.read())
        time_limit = config['time-limit']
        memory_limit = config['memory-limit']

    tc = 1
    while os.path.isfile(tcdir+str(tc)+'.in'):
        # Run test case
        os.system('ln '+tcdir+str(tc)+'.in ~/tmp/in')
        ret = os.system('ulimit -v '+memory_limit+';'+sandbox+'"cd ~/tmp; timeout '+str(
            time_limit/1000)+languages[data['language']].cmd+' < in > out";ulimit -v unlimited')
        os.system('rm ~/tmp/in')
        if ret != 0:
            verdict(data, 408)  # Runtime error
            return

        # Diff the output with the answer
        ret = os.system('diff -w ~/tmp/out '+tcdir+str(tc)+'.out')
        os.system('rm ~/tmp/out')
        if ret != 0:
            verdict(data, 406)  # Wrong answer
            return
        tc += 1

    verdict(data, 202)  # All correct!