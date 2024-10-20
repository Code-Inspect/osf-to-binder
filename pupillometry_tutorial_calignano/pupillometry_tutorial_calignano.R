#clean the R Environment
rm(list = ls())
#set working directory
setwd("~Downloads")
#upload the dataset
data = read.csv("dataset_tutorial.csv", sep =",", stringsAsFactors = T, header = T)
#check 
summary(data)

#optimizing dataframe before dataprocessing
data$average = as.numeric(as.character(data$average))
data$PupilSizeLeft = as.numeric(as.character(data$PupilSizeLeft))
data$PupilSizeRight = as.numeric(as.character(data$PupilSizeRight))
data$familiarization_type= factor(data$familiarization_type,levels=c("labeled","unlabeled"),labels=c("audiovisual","visual"))
data = data[data$time<=1000,] #1000 ms is the maximum duration of a trial
#we replaced missing data (i.e. average = -1) with NA
library(dplyr)
library(naniar)
data = data %>% 
  replace_with_na(replace = list(average = -1))

#exclude NAs from data
data <- data[complete.cases(data$average), ]
summary(data)
nrow(data)


##First degree of freedom
#### plausible value range ]2,8[ - from 1 to 2 DATASETS
library(plyr)
all <-data
all$step <- "implausible"
summary(all)

plausible <-data[data$average>2 & data$average<8,]
plausible$step <- "plausible"
summary(plausible)

all_plausible <- list(all, plausible)

##Second degree of freedom
### Area of Interest - from 2 to 4 DATASETS

AOI_all <- all[all$GazePointX > 200,]
AOI_all <- AOI_all[AOI_all$GazePointX < 800,]
AOI_all <- AOI_all[AOI_all$GazePointY > 0 ,]
AOI_all <- AOI_all[AOI_all$GazePointY <1000,]
AOI_all$step <- "AOI_implausible"
summary(AOI_all)

AOI_plausible <-plausible[plausible$GazePointX > 200,]
AOI_plausible <- AOI_plausible[AOI_plausible$GazePointX < 800,]
AOI_plausible <- AOI_plausible[AOI_plausible$GazePointY > 0 ,]
AOI_plausible <- AOI_plausible[AOI_plausible$GazePointY <1000,]
AOI_plausible$step <- "AOI_plausible"
summary(AOI_plausible)

AOI <- list(AOI_all, AOI_plausible)

##third degree of freedom 
### median baseline from 4 to 12 DATASETS
### 3 median baseline i.e. initial time window for each session ,id, familiarization type
### i.e. 16, 100, 200 ms
library(plyr)
degrees =c(1, 1:6, 1:12)
universe_one <-list(all_plausible, AOI)
#16 ms baseline 6 DATASETS
for (k in 1:2) {
  for (i in 1:2) {
    dg = 16
    universe_one[[k]][[i]]<-ddply(universe_one[[k]][[i]],.(id, familiarization_type,session),
                                  transform,baseline = average - median(average[1]), na.rm = T)
    
    cat("\n\nk =",k,"i =",i,"j =",dg,
        "\nbaby 2 =",universe_one[[k]][[i]][universe_one[[k]][[i]]$id=="2","baseline"][1],
        "\nbaby 14 =",universe_one[[k]][[i]][universe_one[[k]][[i]]$id=="14","baseline"][1]
        )
  }
}

#100 ms baseline 6 DATASETS
universe_two <-list(all_plausible, AOI)
for (k in 1:2) {
  for (i in 1:2) {
    dg = 100
    universe_two[[k]][[i]]<-ddply(universe_two[[k]][[i]],.(id, familiarization_type,session),
                                  transform,baseline = average - median(average[1:min(6:length(time))]), na.rm = T)
    cat("\n\nk =",k,"i =",i,"j =",dg,
        "\nbaby 2 =",universe_one[[k]][[i]][universe_one[[k]][[i]]$id=="2","baseline"][1],
        "\nbaby 14 =",universe_one[[k]][[i]][universe_one[[k]][[i]]$id=="14","baseline"][1])
  }
}


#200 ms baseline 6 DATASETS
universe_three <-list(all_plausible, AOI)

for (k in 1:2) {
  for (i in 1:2) {
    dg = 200
    universe_three[[k]][[i]]<-ddply(universe_three[[k]][[i]],.(id, familiarization_type,session),
                                    transform,baseline = average - median(average[1:min(12:length(time))]), na.rm = T)
    cat("\n\nk =",k,"i =",i,"j =",dg,
        "\nbaby 2 =",universe_one[[k]][[i]][universe_one[[k]][[i]]$id=="2","baseline"][1],
        "\nbaby 14 =",universe_one[[k]][[i]][universe_one[[k]][[i]]$id=="14","baseline"][1])
  }
}

#multiverse
multiverse <- list(universe_one, universe_two, universe_three)

##########################################################################################################
#The impact of dataprocessing on statistical modeling
library(mgcv)
library(itsadug)
library(sjPlot)
par(mfrow=c(5,3), cex=.7, mar=c(2,3,2,2))
for(k in 1:3){ #multiverse 3 levels
  for(i in 1:2){ # universe 2  levels 
    for(j in 1:2){ # all_plausible/AOI 2 levels
      
      TIME<-bam(baseline~ familiarization_type+ s(time, by= familiarization_type, k=20) + 
                  s(time, by= session, k=20)+
                  s(time, id, bs='fs', m=1),#+ s(time, familiarization_type, bs = "fs",m = 1),
                data= multiverse[[k]][[i]][[j]], discrete=TRUE, nthreads=40)
      multi_acf <-  acf_resid(TIME) #autocorrelation check
      
      multi_time <- plot_diff(TIME, view="time", rm.ranef=TRUE, 
                              comp=list(familiarization_type=c("visual","audiovisual")), 
                              v0=0, col.diff = alpha(1), # remove difference marking
                              main="")
      #plot by trial 
      multi_time2 <- plot_smooth(TIME, view="time", plot_all=c("session"), 
                                 rm.ranef=F,
                                 rug=F, shade=T,  add=F , lty=c(1,1), lwd=4)
      
       
    }
  }
  
}
