from setuptools import setup

setup(
    name='Pyweek39',
    options={
        'build_apps': {
            'gui_apps': {
                'pyweek39': 'run_game.py',
            },
            'platforms': ['manylinux2014_x86_64', 'macosx_10_6_x86_64', 'win_amd64'],
            #'platforms': ['win_amd64'],
            # Set up output logging, important for GUI apps!
            'log_filename': './logs/output.log',
            'log_append': False,
            'include_modules': [
                'certifi',
            ],
            # Specify which files are included with the distribution
            'include_patterns': [
                'assets/**/*',
                'user_config.json',
                'map.json',
                '*.png'
            ],
            # Include the OpenGL renderer and OpenAL audio plug-in
            'plugins': [
                'pandagl',
                'p3openal_audio',
                'p3ffmpeg',
                'p3assimp'
            ],
            'prefer_discrete_gpu': True,
        }
    }
)
