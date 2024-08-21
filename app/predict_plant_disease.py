import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
from torchvision import transforms

NUM_CLASSES = 38
PATH = "/Users/jonathansuru/PycharmProjects/mazao/models/plant-disease-model.pth"

CLASS_NAMES = [
    "Apple___Apple_scab",
    "Apple___Black_rot",
    "Apple___Cedar_apple_rust",
    "Apple___healthy",
    "Blueberry___healthy",
    "Cherry_(including_sour)___Powdery_mildew",
    "Cherry_(including_sour)___healthy",
    "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot",
    "Corn_(maize)___Common_rust_",
    "Corn_(maize)___Northern_Leaf_Blight",
    "Corn_(maize)___healthy",
    "Grape___Black_rot",
    "Grape___Esca_(Black_Measles)",
    "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)",
    "Grape___healthy",
    "Orange___Haunglongbing_(Citrus_greening)",
    "Peach___Bacterial_spot",
    "Peach___healthy",
    "Pepper,_bell___Bacterial_spot",
    "Pepper,_bell___healthy",
    "Potato___Early_blight",
    "Potato___Late_blight",
    "Potato___healthy",
    "Raspberry___healthy",
    "Soybean___healthy",
    "Squash___Powdery_mildew",
    "Strawberry___Leaf_scorch",
    "Strawberry___healthy",
    "Tomato___Bacterial_spot",
    "Tomato___Early_blight",
    "Tomato___Late_blight",
    "Tomato___Leaf_Mold",
    "Tomato___Septoria_leaf_spot",
    "Tomato___Spider_mites Two-spotted_spider_mite",
    "Tomato___Target_Spot",
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
    "Tomato___Tomato_mosaic_virus",
    "Tomato___healthy",
]


# base class for the model
class ImageClassificationBase(nn.Module):
    """ """
    def training_step(self, batch):
        """

        :param batch:

        """
        images, labels = batch
        out = self(images)  # Generate predictions
        return F.cross_entropy(out, labels)

    def validation_epoch_end(self, outputs):
        """

        :param outputs:

        """
        batch_losses = [x["val_loss"] for x in outputs]
        batch_accuracy = [x["val_accuracy"] for x in outputs]
        epoch_loss = torch.stack(batch_losses).mean()  # Combine loss
        epoch_accuracy = torch.stack(batch_accuracy).mean()
        return {
            "val_loss": epoch_loss,
            "val_accuracy": epoch_accuracy,
        }  # Combine accuracies

    def epoch_end(self, epoch, result):
        """

        :param epoch:
        :param result:

        """
        print(
            "Epoch [{}], last_lr: {:.5f}, train_loss: {:.4f}, val_loss: {:.4f}, val_acc: {:.4f}".format(
                epoch,
                result["lrs"][-1],
                result["train_loss"],
                result["val_loss"],
                result["val_accuracy"],
            )
        )


# Architecture for training


# convolution block with BatchNormalization
def ConvBlock(in_channels, out_channels, pool=False):
    """

    :param in_channels:
    :param out_channels:
    :param pool:  (Default value = False)

    """
    layers = [
        nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1),
        nn.BatchNorm2d(out_channels),
        nn.ReLU(inplace=True),
    ]
    if pool:
        layers.append(nn.MaxPool2d(4))
    return nn.Sequential(*layers)


# resnet architecture
class ResNet9(ImageClassificationBase):
    """ """
    def __init__(self, in_channels, num_diseases):
        super().__init__()

        self.conv1 = ConvBlock(in_channels, 64)
        self.conv2 = ConvBlock(64, 128, pool=True)  # out_dim : 128 x 64 x 64
        self.res1 = nn.Sequential(ConvBlock(128, 128), ConvBlock(128, 128))

        self.conv3 = ConvBlock(128, 256, pool=True)  # out_dim : 256 x 16 x 16
        self.conv4 = ConvBlock(256, 512, pool=True)  # out_dim : 512 x 4 x 44
        self.res2 = nn.Sequential(ConvBlock(512, 512), ConvBlock(512, 512))

        self.classifier = nn.Sequential(
            nn.MaxPool2d(4), nn.Flatten(), nn.Linear(512, num_diseases)
        )

    def forward(self, xb):  # xb is the loaded batch
        """

        :param xb:

        """
        out = self.conv1(xb)
        out = self.conv2(out)
        out = self.res1(out) + out
        out = self.conv3(out)
        out = self.conv4(out)
        out = self.res2(out) + out
        out = self.classifier(out)
        return out


def load_model(model_class, path, num_classes):
    """

    :param model_class:
    :param path:
    :param num_classes:

    """
    # Determine the device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Create an instance of the model
    model = model_class(3, num_classes)  # Assuming 3 input channels

    # Load the state dict
    state_dict = torch.load(path, map_location=device, weights_only=True)
    model.load_state_dict(state_dict)

    # Move model to the appropriate device
    model = model.to(device)

    # Set the model to evaluation mode
    model.eval()

    return model


def predict(image_path):
    """

    :param image_path:

    """
    model = load_model(ResNet9, PATH, NUM_CLASSES)
    # Load and preprocess the image
    image = Image.open(image_path)
    transform = transforms.Compose(
        [transforms.Resize((256, 256)), transforms.ToTensor()]
    )
    image = transform(image).unsqueeze(0)

    # Determine the device
    device = next(model.parameters()).device
    image = image.to(device)

    # Make prediction
    with torch.no_grad():
        output = model(image)
        _, predicted = torch.max(output, 1)

    return CLASS_NAMES[predicted.item()]
