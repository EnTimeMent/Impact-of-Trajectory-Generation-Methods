import builtins
import decimal
import logging
import sys
import simplejson
import utils.distributed as dist
import os
import calendar
import time

from torch.utils.tensorboard import SummaryWriter


def _suppress_print():
    """
    Suppresses printing from the current process.
    """

    def print_pass(*objects, sep=" ", end="\n", file=sys.stdout, flush=False):
        pass

    builtins.print = print_pass


def setup_logging(cfg):
    """
    Sets up the logging for multiple processes. Only enable the logging for the
    master process, and suppress logging for the non-master processes.
    """
    # Set up logging format.
    _FORMAT = "[%(levelname)s: %(filename)s: %(lineno)4d]: %(message)s"

    if  dist.is_master_proc(cfg.NUM_GPUS):
        # Enable logging for the master process.
        logging.root.handlers = []
        logging.basicConfig(
            level=logging.INFO, format=_FORMAT, stream=sys.stdout
        )
    else:
        # Suppress logging for non-master processes.
        _suppress_print()


def get_logger(name):
    """
    Retrieve the logger with the specified name or, if name is None, return a
    logger which is the root logger of the hierarchy.
    Args:
        name (string): name of the logger.
    """
    return logging.getLogger(name)


def log_json_stats(stats):
    """
    Logs json stats.
    Args:
        stats (dict): a dictionary of statistical information to log.
    """
    stats = {
        k: decimal.Decimal("{:.6f}".format(v)) if isinstance(v, float) else v
        for k, v in stats.items()
    }
    json_stats = simplejson.dumps(stats, sort_keys=True, use_decimal=True)
    logger = get_logger(__name__)
    logger.info("json_stats: {:s}".format(json_stats))


class TFLogger():
    def __init__(self,cfg):
        self.cfg = cfg
        if dist.is_master_proc(cfg.NUM_GPUS):
            path = os.path.join(cfg.LOG_DIR,str(calendar.timegm(time.gmtime())))
            os.mkdir(path)
            self.writer = SummaryWriter(path)
            
    def add_scalar(self,name,value,step):
        if (step+1)%self.cfg.LOG_PERIOD==0:
            if dist.is_master_proc(self.cfg.NUM_GPUS):
                self.writer.add_scalar(name,value,step)
    
    def close(self):
        if dist.is_master_proc(self.cfg.NUM_GPUS):
            self.writer.close()