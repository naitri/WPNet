import torch
import torch.nn as nn
from torchvision import transforms, utils
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader, random_split
from model import WPNet, PTModel
from dataloader import SastaDataset, Rescale, ToTensor, Normalize
from train import Solver

# NOTE :normalize x,y,z values - or use different network
# Maybe we are trying to over optimize the mse loss - maybe this works fine and maybe we should compare the obstacle free distance moved ??

def main():

    # Variable initialization
    data_folder = 'manual_combo_0124'
    save_model_path = 'final_models/'
    txt_file = f"../Dataset/{data_folder}/{data_folder}/airsim_rec.txt"
    img_dir = f"../Dataset/{data_folder}/{data_folder}/images"
    batch_size = 16
    epochs = 25
    desired_image_input = (3, 216, 384)
    transform=transforms.Compose([Rescale((desired_image_input[1], desired_image_input[2])), ToTensor(), transforms.Normalize(mean=[0.5,0.5,0.5], std=[0.5,0.5,0.5])])
    
    # Generating the dataloader
    dataset = SastaDataset(txt_file, img_dir, transform)
    train_size = int(0.8 * len(dataset))
    test_size = len(dataset) - train_size
    train_dataset, test_dataset = random_split(dataset, [train_size, test_size])
    trainloader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=0)
    testloader = DataLoader(test_dataset, batch_size=batch_size, shuffle=True, num_workers=0)

    # Loading the pretrained monocular depth estimation model 
    tensor = torch.zeros((batch_size, desired_image_input[0], desired_image_input[1], desired_image_input[2]))
    model = PTModel().float()
    model.load_state_dict(torch.load("models/nyu.pt"))
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    wpnet = WPNet(tuple(tensor.shape), model).to(device)
    # wpnet.load_state_dict(torch.load("final_models/wpnet.pt"))

    # Model training
    torch.cuda.empty_cache()
    solver = Solver(wpnet, trainloader, epochs, device, lr=0.001)
    trained_model = solver.train(data_folder)
    
    # Not saving the full model - only the state dictionary - might modify to add the current state of model - like epochs trained, batch size etc.
    torch.save(trained_model.state_dict(), save_model_path + 'wpnet.pt')

if __name__ == "__main__":
    main()