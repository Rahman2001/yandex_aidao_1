from utils import *
from trainer import Trainer
import os
from pathlib import Path

def get_arguments(base_path):
    """
    handle arguments from commandline.
    some other hyper parameters can only be changed manually (such as model architecture,dropout,etc)
    notice some arguments are global and take effect for the entire three phase training process, while others are determined per phase
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--base_path', default=base_path)
    parser.add_argument('--seed', type=int, default=55555555)
    parser.add_argument('--dataset_name', type=str, default="ucla")
    parser.add_argument('--cuda', default=True)
    parser.add_argument('--log_dir', type=str, default=os.path.join(base_path, 'runs'))
    parser.add_argument('--random_TR', default=True)
    parser.add_argument('--intensity_factor', default=1)
    parser.add_argument('--perceptual_factor', default=1)
    parser.add_argument('--reconstruction_factor', default=1)
    parser.add_argument('--transformer_hidden_layers', default=2)
    parser.add_argument('--fine_tune_task',
                        default='binary_classification',
                        choices=['regression','binary_classification'],
                        help='fine tune model objective. choose binary_classification in case of a binary classification task')
    parser.add_argument('--train_split', default=0.7)
    parser.add_argument('--val_split', default=0.15)
    parser.add_argument('--running_mean_size', default=5000)


    ##phase 1
    parser.add_argument('--task_phase1', type=str, default='autoencoder_reconstruction')
    parser.add_argument('--batch_size_phase1', type=int, default=4)
    parser.add_argument('--validation_frequency_phase1', type=int, default=1000)
    parser.add_argument('--nEpochs_phase1', type=int, default=10)
    parser.add_argument('--augment_prob_phase1', default=0)
    parser.add_argument('--weight_decay_phase1', default=1e-7)
    parser.add_argument('--lr_init_phase1', default=1e-3)
    parser.add_argument('--lr_gamma_phase1', default=0.97)
    parser.add_argument('--lr_step_phase1', default=500)
    parser.add_argument('--sequence_length_phase1', default=1)
    parser.add_argument('--workers_phase1', default=4)

    ##phase 2
    parser.add_argument('--task_phase2', type=str, default='transformer_reconstruction')
    parser.add_argument('--batch_size_phase2', type=int, default=1)
    parser.add_argument('--validation_frequency_phase2', type=int, default=500)
    parser.add_argument('--nEpochs_phase2', type=int, default=5)
    parser.add_argument('--augment_prob_phase2', default=0)
    parser.add_argument('--weight_decay_phase2', default=1e-7)
    parser.add_argument('--lr_gamma_phase2', default=0.97)
    parser.add_argument('--lr_step_phase2', default=1000)
    parser.add_argument('--sequence_length_phase2', default=20)
    parser.add_argument('--workers_phase2', default=1)

    ##phase 3
    parser.add_argument('--task_phase3', type=str, default='fine_tune')
    parser.add_argument('--batch_size_phase3', type=int, default=3)
    parser.add_argument('--validation_frequency_phase3', type=int, default=200)
    parser.add_argument('--nEpochs_phase3', type=int, default=30)
    parser.add_argument('--augment_prob_phase3', default=0)
    parser.add_argument('--weight_decay_phase3', default=1e-2)
    parser.add_argument('--lr_init_phase3', default=1e-4)
    parser.add_argument('--lr_gamma_phase3', default=0.9)
    parser.add_argument('--lr_step_phase3', default=1500)
    parser.add_argument('--sequence_length_phase3', default=20)
    parser.add_argument('--workers_phase3', default=0)
    args = parser.parse_args()
    return args

def setup(cuda_num):
    cuda_num = str(cuda_num)
    os.environ["CUDA_VISIBLE_DEVICES"] = cuda_num
    base_path = os.getcwd()
    os.makedirs(os.path.join(base_path,'experiments'),exist_ok=True)
    os.makedirs(os.path.join(base_path,'runs'),exist_ok=True)
    os.makedirs(os.path.join(base_path, 'splits'), exist_ok=True)
    return base_path

def run_phase(args,loaded_model_weights_path,phase_num,phase_name):
    """
    main process that runs each training phase
    :return path to model weights (pytorch file .pth) aquried by the current training phase
    """
    experiment_folder = '{}_{}_{}'.format(args.dataset_name,phase_name,datestamp())
    experiment_folder = Path(os.path.join(args.base_path,'experiments',experiment_folder))
    os.makedirs(experiment_folder)
    setattr(args,'loaded_model_weights_path_phase' + phase_num,loaded_model_weights_path)
    args.experiment_folder = experiment_folder
    args.experiment_title = experiment_folder.name
    fine_tune_task = args.fine_tune_task
    args_logger(args)
    args = sort_args(phase_num, vars(args))
    S = ['train','val']
    trainer = Trainer(sets=S,**args)
    trainer.training()
    if phase_num == '3' and not fine_tune_task == 'regression':
        critical_metric = 'accuracy'
    else:
        critical_metric = 'loss'
    model_weights_path = os.path.join(trainer.writer.experiment_folder,trainer.writer.experiment_title + '_BEST_val_{}.pth'.format(critical_metric))
    return model_weights_path

def test(args,model_weights_path):
    experiment_folder = '{}_{}_{}'.format(args.dataset_name, 'test_{}'.format(args.fine_tune_task), datestamp())
    experiment_folder = os.path.join(args.base_path,'tests', experiment_folder)
    os.makedirs(experiment_folder)
    trainer = Trainer(experiment_folder, '3', args, ['test'], model_weights_path)
    trainer.testing()

def main(base_path):
    args = get_arguments(base_path)
    # pretrain step1
    print('starting phase 1...')
    model_weights_path_phase1 = run_phase(args,None,'1','autoencoder_reconstruction')
    print('finishing phase 1...')
    #pretrain step2
    print('starting phase 2...')
    model_weights_path_phase2 = run_phase(args,model_weights_path_phase1, '2', 'tranformer_reconstruction')
    print('finishing phase 2...')
    #fine tune
    print('starting phase 3...')
    model_weights_path_phase3 = run_phase(args, model_weights_path_phase2,'3','fine_tune_{}'.format(args.fine_tune_task))
    print('finishing phase 3...')
    #test
    test(args, model_weights_path_phase3)




if __name__ == '__main__':
    base_path = setup(cuda_num=0)
    main(base_path)

