# Programming language class
# Must contain a command to get version and run code
# Compile command is optional
class language:
    def __init__(self, version, run, compile=None):
        self.version = version
        self.run = run
        self.compile = compile


# TODO: Support more languages
languages = {
    # Language       Version                                     Run             Compile
    'cpp':  language('g++ --version | head -n1 | cut -d" " -f3', './main',       'g++ main.cpp -o main -O2'),
    'py':   language('python -V | cut -d" " -f2',                'python main.py'),
    'java': language('java --version | head -n1 | cut -d" " -f2','java main',    'javac main.java'),
    'c':    language('gcc --version | head -n1 | cut -d" " -f3', './main',       'gcc main.c -o main -O2'),
    'cs':   language('mcs --version | cut -d" " -f5',            'mcs main.cs',  'mono main.exe'),
    'js':   language('node -v | cut -c 2-',                      'node main.js'),
    'rb':   language('ruby -v | cut -d" " -f2',                  'ruby main.ruby'),
    'pl':   language('perl -v | awk -F"[()]" \'/This/ {print $2}\' | cut -c 2-', 'perl main.pl'),
    'php':  language('php -v | head -n1 | cut -d" " -f2',        'php main.php'),
    'go':   language('go version | cut -d" " -f3 | cut -c 3-',   './main',       'go build main.go'),
    'rs':   language('rustc -V | cut -d" " -f2',                 './main',       'rustc main.rs'),
    'lua':  language('lua -v | cut -d" " -f2',                   'lua main.lua'),
    'jl':   language('julia -v | cut -d" " -f3',                 'julia main.jl'),
    'sh':   language('bash --version | head -n1 | cut -d" " -f4','bash main.sh', 'chmod +x main.sh')
}
