import simpy
import logging

class GPU:
    def __init__(self, env, id, free_mem, free_gpu_cores):
        self.env = env
        self.id = id
        self.free_mem = free_mem
        self.free_gpu_cores = free_gpu_cores

class CloudJob:
    def __init__(self, env, execution_time, gpu_cores, gpu_memory):
        self.env = env
        self.id = id(self)
        self.execution_time = execution_time
        self.gpu_cores = gpu_cores
        self.gpu_mem = gpu_memory

def schedule_jobs(env, jobs, gpu_array):
    for job in jobs:
        # Check if there is an available GPU with enough resources at the scheduled time
        available_gpu = None
        for gpu in gpu_array:
            if gpu.free_gpu_cores >= job.gpu_cores and gpu.free_mem >= job.gpu_mem:
                available_gpu = gpu
                break
        if available_gpu:
            # allocate resources
            available_gpu.free_gpu_cores -= job.gpu_cores
            available_gpu.free_mem -= job.gpu_mem
            # Create and start the job process
            env.process(job_action(env, job, available_gpu))
        else:
            # log
            print(f'No available GPU for Job {job.id}')
    yield env.timeout(0)
    
def job_action(env, job, gpu):
    yield env.timeout(job.execution_time)
    # release resources
    gpu.free_gpu_cores += job.gpu_cores
    gpu.free_mem += job.gpu_mem
    # log
    print(f'Job {job.id} completed on GPU {gpu.id}')

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%m-%d %H:%M:%S')

# Test with sample data
env = simpy.Environment()
jobs = [CloudJob(env, 15, 1, 1), CloudJob(env, 25, 2, 2), CloudJob(env, 30, 3, 3),
        CloudJob(env, 10, 1, 2), CloudJob(env, 20, 2, 3), CloudJob(env, 35, 3, 4),
        CloudJob(env, 5, 1, 1), CloudJob(env, 15, 2, 2), CloudJob(env, 20, 3, 3),
        CloudJob(env, 25, 1, 2), CloudJob(env, 30, 2, 3)]
gpus = [GPU(env, 1, 8, 2), GPU(env, 2, 8, 2)]
env.process(schedule_jobs(env, jobs, gpus))
env.run()
