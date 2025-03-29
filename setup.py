from setuptools import setup
import platform

platforms = {
    "Linux": ['manylinux2014_x86_64'],
    "Windows": ['win_amd64'],
    "Darwin": ['macosx_10_6_x86_64'],
}

setup(
    name='Flow',
    options={
        'build_apps': {
            'gui_apps': {
                'flow': 'run_game.py',
            },
            'platforms': platforms.get(platform.system(), ["win_amd64"]), # default to windows
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
