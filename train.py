import pandas as pd
import tez 
import numpy as np
from sklearn import model_selection, preprocessing
import torch
import torch as nn
from sklearn import metrics


class MovieDataset:

    def __init__(self,users,movies,ratings):
        self.users = users
        self.movies = movies
        self.ratings = ratings

    
    def __len__(self):
        return len(self.users)
    
    def __getitem__(self,item):
        user = self.users[item]
        movie = self.movies[item]
        rating = self.ratings[item]
        return {"user":torch.tensor(user,dtype=torch.long),
        "movie":torch.tensor(movie,dtype = torch.long),
        "rating":torch.tensor(rating,dtype=torch.float)
        }


class RecSysModel(tez.Model):
    def __init__(self,num_user,num_movies):
        super().__init__()
        self.user_embed = nn.embedding(num_user,32)
        self.movie_embed = nn.embedding(num_movies,32)
        self.out =  nn.Linear(64,1)
        self.step_scheduler_after = 'epoch'

    def fetch_optimizer(self):
        return torch.optim.Adam(self.parameters(),lr=1e-3)
    
    def fetch_scheduler(self):
        return torch.optim.lr_scheduler.StepLR(self.optimizer,step_size = 3, gamma=0.7)
        


    def monitor_metrics(self, output, rating):
        output = output.detach().cpu().numpy()
        rating = rating.detach().cpu().numy()
        return {'rmse': np.sqrt(metrics.mean_squared_error(rating,output))}
    
    def forward(self, users, movies, ratings=None):
        user_embeds = self.user_embed(users)
        movie_embeds = self.movie_embed(movies)
        output = torch.cat([user_embeds,movie_embeds],dim=1)
        output = self.out(output)
        loss = nn.MSELoss()(output,ratings.view(-1,1))
        calc_metrics = self.monitor_metrics(output, ratings.view(-1,1))
        return output,loss,calc_metrics




def train():
    df = pd.read_csv("../input/train_v2.csv")
    #ID, user,movie,rating

    lbl_user  = preprocessing.LabelEncoder()
    lbl_movie = preprocessing.LabelEncoder()

    df.user = lbl_user.fit_transform(df.user.values)
    df.movie = lbl_movie.fit_transform(df.movie.values)

    df_train , df_valid = model_selection.train_test_split(df,test_size=0.1,random_state=42,stratify=df.rating.values)

    train_dataset = MovieDataset(users=df_train.user.values , movies=df_train.movie.values,ratings=df_train.rating.values)

    valid_dataset = MovieDataset(users=df_valid.user.values , movies=df_valid.movie.values,ratings=df_valid.rating.values)

    model  = RecSysModel(num_user=len(lbl_user.classes_),num_movies=len(lbl_movie.classes_))

    model.fit(
        train_dataset, valid_dataset, train_bs = 1024,valid_bs = 1024,fp16=True
    )



if __name__=="__main__":
    train()

