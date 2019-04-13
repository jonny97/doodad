"""
A simplified API for invoking commands via doodad.

Here is a simple hello world example using run_command:

result = launch_api.run_command(
    command='echo helloworld',
    mode=mode.LocalMode(),
)
"""
import os

from doodad.darchive import archive_builder_docker as archive_builder
from doodad import mount
from doodad import mode as launch_mode


def run_command(
        command,
        cli_args=None,
        mode=launch_mode.LocalMode(),
        mounts=tuple(),
        return_output=False,
        verbose=False,
        docker_image='ubuntu:18.04'
    ):
    """
    Runs a shell command using doodad via a specified launch mode.

    Args:
        command (str): A shell command
        cli_args (str): Command line args to pass
        mode (LaunchMode): A LaunchMode object
        mounts (tuple): A list/tuple of Mount objects
        return_output (bool): If True, returns stdout as a string.
            Do not use if the output will be large.
    
    Returns:
        A string output if return_output is True,
        else None
    """
    with archive_builder.temp_archive_file() as archive_file:
        archive = archive_builder.build_archive(archive_filename=archive_file,
                                                payload_script=command,
                                                verbose=False, 
                                                docker_image=docker_image,
                                                mounts=mounts)
        cmd = archive
        if cli_args:
            cmd = archive + ' -- ' + cli_args
        result = mode.run_script(cmd, return_output=return_output, verbose=verbose)
    if return_output:
        result = archive_builder._strip_stdout(result)

    return result


def run_commands(
        command,
        cli_args=(None,),
        mode=launch_mode.LocalMode(),
        mounts=tuple(),
        return_output=False,
        verbose=False,
        docker_image='ubuntu:18.04'
    ):
    """
    Run multiple commands in one call, each with potentially different
    command line arguments. This function will be faster than running
    run_command() N times.

    To launch a command N times without args, pass [None]*N as cli_args.
    To launch a command N times with args, pass in a list of command line arguments
    as cli_args -- the script will be run once per set of arguments.

    Args:
        command (str): A shell command
        cli_args (list[str]): A list of command line arguments to pass,
            one per call. The command will be called once PER item in this list.
        mode (LaunchMode): A LaunchMode object
        mounts (tuple): A list/tuple of Mount objects
        return_output (bool): If True, returns stdout as a string.
            Do not use if the output will be large.

    Returns:
        A string output if return_output is True,
        else None
    """
    results = []
    with archive_builder.temp_archive_file() as archive_file:
        archive = archive_builder.build_archive(archive_filename=archive_file,
                                                payload_script=command,
                                                verbose=False, 
                                                docker_image=docker_image,
                                                mounts=mounts)
        cmd = archive
        for cli_arg in cli_args:
            if cli_arg:
                cmd = archive + ' -- ' + cli_arg
            results.append(mode.run_script(cmd, return_output=return_output, verbose=verbose))
    if return_output:
        results = [archive_builder._strip_stdout(result) for result in results]
    return results


def run_python(
        target,
        target_mount_dir='target',
        mounts=tuple(),
        docker_image='python:3',
        run_multiple=True,
        **kwargs
    ):
    """
    Runs a python script using doodad via a specified launch mode.

    Args:
        target (str): Path to a python script. i.e. '/home/user/hello.py'
        target_mount_dir (str): Directory to mount the target inside container.
            Default is 'target'. Changing this is usually unnecessary.
        mounts (tuple): A list/tuple of Mount objects
        run_multiple (bool): If True, runs launches the python command multiple times.
            This is faster than N separate calls to run_python.
            In order for this command to work, cli_args must be passed in as a list 
            The command will be launched once per set of arguments in the list.
            (see documentation for run_commands for more details)
        **kwargs: Arguments to run_command
    
    Returns:
        A string output if return_output is True,
        else None
    """
    target_dir = os.path.dirname(target)
    target_mount_dir = os.path.join(target_mount_dir, os.path.basename(target_dir))
    target_mount = mount.MountLocal(local_dir=target_dir, mount_point=target_mount_dir)
    mounts = list(mounts) + [target_mount]
    target_full_path = os.path.join(target_mount.mount_point, os.path.basename(target))
    command = make_python_command(
        target_full_path,
    )
    if run_multiple:
        return run_commands(command, docker_image=docker_image, mounts=mounts, **kwargs)
    else:
        return run_command(command, docker_image=docker_image, mounts=mounts, **kwargs)


def make_python_command(
        target,
        python_cmd='python',
    ):
    cmd = '%s %s' % (python_cmd, target)
    return cmd
