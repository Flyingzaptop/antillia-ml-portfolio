from pathlib import Path
import torch,numpy as np
ROOT=Path(__file__).resolve().parent
COLS=['Air temperature [K]','Process temperature [K]','Rotational speed [rpm]','Torque [Nm]','Tool wear [min]']
KEYS=['air_temperature','process_temperature','rotational_speed','torque','tool_wear']
def network():return torch.nn.Sequential(torch.nn.Linear(5,12),torch.nn.Tanh(),torch.nn.Linear(12,2),torch.nn.Tanh(),torch.nn.Linear(2,12),torch.nn.Tanh(),torch.nn.Linear(12,5))
def scores(model,x):
 with torch.no_grad():return ((model(torch.tensor(x,dtype=torch.float32)).numpy()-x)**2).mean(1)
