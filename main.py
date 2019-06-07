"""
Alaska Satellite Facility
Convolutional Neural Network
McKade Sorensen (Douglas)
05/21/2019

main.py, runs the code for AI_Project. The first time the program runs it'll create the files
needed. After its ran once the dataset folder (with all the SAR images) needs to be extracted into
AI_Project. asf_cnn.h5 and labels.json both need to be moved there into the AI_Project folder.
"""

import os
from argparse import ArgumentParser, Namespace

# import img_functions
from src.asf_cnn import test_model, train_model
from src.model import create_model, load_model, path_from_model_name
from src.plots import plot_confusion_chart, plot_predictions
from src.reports import write_dict_to_csv


def main():
    # Passing the file directory main.py is located to be used for the rest of the program
    img_functions.create_directories()
    img_functions.move_incorrect_predictions_back()
    img_functions.move_data_back()
    # Setting up SAR data
    img_functions.sar_data_setup()
    # The paramerter is the percent of the data that is going to be test data.
    img_functions.test_training_data_percent(30)
    # Creating and running the CNN.
    cnn.cnn()
    img_functions.move_data_back()
    img_functions.move_incorrect_predictions_back()


def train_wrapper(args: Namespace) -> None:
    model_name = args.model

    if args.cont:
        model = load_model(model_name)
        history = model.__asf_model_history
    else:
        model_path = path_from_model_name(model_name)
        if not args.overwrite and os.path.isfile(model_path):
            print(f"File {model_name} already exists!")
            return
        model = create_model(model_name)
        history = {"loss": [], "acc": [], "val_loss": [], "val_acc": []}

    train_model(model, history, args.dataset, args.epochs)


def test_wrapper(args: Namespace) -> None:
    model_name = args.model
    model = load_model(model_name)

    details, confusion_matrix = test_model(model, args.dataset)

    model_dir = os.path.dirname(path_from_model_name(model_name))
    with open(os.path.join(model_dir, 'results.csv'), 'w') as f:
        write_dict_to_csv(details, f)

    plot_confusion_chart(confusion_matrix)
    plot_predictions(details['Percent'], args.dataset)


if __name__ == '__main__':
    p = ArgumentParser()
    sp = p.add_subparsers()

    # Arguments for train mode
    train = sp.add_parser('train', help='Train a new model')
    train.add_argument('model', help='Name of the model to save: example_net')
    train.add_argument('dataset', nargs='?', default='dataset_calibrated')
    train.add_argument(
        '--overwrite',
        '-o',
        action='store_true',
        help='Replace the file if it exists'
    )
    train.add_argument(
        '--continue',
        '-c',
        action='store_true',
        dest='cont',
        help='Continue training from existing model'
    )
    train.add_argument('--epochs', '-e', type=int, default=10)
    train.set_defaults(func=train_wrapper)

    # Arguments for test mode
    test = sp.add_parser('test', help='Test an existing model')
    test.add_argument('model', help='Name of the trained model')
    test.add_argument('dataset', nargs='?', default='dataset_calibrated')
    test.set_defaults(func=test_wrapper)

    # Parse and execute selected function
    args = p.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        p.print_help()