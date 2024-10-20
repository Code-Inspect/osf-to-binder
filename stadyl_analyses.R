# ==========================================
# This script analyses data of Study 2 
# ==========================================

# load packages
library(haven)
library(psych)
library(dplyr)
library(car)
library(interactions)
library(ggplot2)
library(ggfortify)
library(lm.beta)
library(reghelper)
library(stats)
library(Hmisc)


# read in data
data <- read_sav("/Users/maria/Documents/projects/_collabs/anticip_status/data/StadyL_Study2.sav")
data <- as.data.frame(data)


# ------------------
# Data wrangling
# ------------------

# recode values for missing data (-9, -999) in whole dataset as NA
data <- data %>% mutate_all(~na_if(., -999))
data <- data %>% mutate_all(~na_if(., -9))

# age
# -----

data$age <- data$aget1

# sex
# -------

# recode variable
data$sex[data$sext1 == 0] <- 1 # men
data$sex[data$sext1 == 1] <- 0 # women

# perceived status loss
# ----------------------

# calculate mean
data$sc <- rowMeans(data[,c("SE09_01t2", "SE09_02t2")], na.rm = T) # wave 2


# upward mobility belief
# -------------------------------

# recode items so that higher values indicate higher mobility beliefs
data$SE03_05t2r <- 6-data$SE03_05t2
data$SE03_06t2r <- 6-data$SE03_06t2

# calculate mean future items
data$mob <- rowMeans(data[,c("SE03_01t2", "SE03_02t2", "SE03_03t2", 
                             "SE03_04t2", "SE03_05t2r","SE03_06t2r")], na.rm = T) 


# life satisfaction
# ------------------

# calculate mean score on life satistfaction scale
data$ls.1 <- rowMeans(data[,c("SE11_01", "SE11_02",  "SE11_03", "SE11_04", 
                              "SE11_05")], na.rm = T) # wave 1

data$ls.2 <- rowMeans(data[,c("SE11_01t2", "SE11_02t2",  "SE11_03t2", "SE11_04t2", 
                              "SE11_05t2")], na.rm = T) # wave 2

# participant exclusion I
# ------------------------

# demographics before data exclusion 
psych::describe(data$age)
table(data$sex)
prop.table(table(data$sex))

# exclude participants who have missing data 
data <- subset(data, !is.na(sc)) 
data <- subset(data, !is.na(mob)) 
data <- subset(data, !is.na(ls.1)) 
data <- subset(data, !is.na(ls.2)) 

# ------------------------
# Descriptive statistics
# ------------------------

# demographics after data exclusion 
psych::describe(data$age)
table(data$sex)
prop.table(table(data$sex))

# descriptives M and SD for Table 2
psych::describe(data[c("age", "sex", "SESt1", "sc", "mob", "ls.1", "ls.2")])

# correltations for Table 2
rcorr(as.matrix(data[c("age", "sex", "SESt1", "sc", "mob", "ls.1", "ls.2")]))

# ----------------------
# Moderated regression 
# ----------------------

# center variables
data$ls.1c <- data$ls.1 - 3.57
data$sc.c  <- scale(data$sc,   center = T, scale = F)
data$mob.c <- scale(data$mob,  center = T, scale = F)
data$age.c <- scale(data$age,  center = T, scale = F)

# define interaction variable
data$sc_mob <- data$sc.c*data$mob.c


# model without covariates
# -------------------------------

# definde and fit model
m1 <- ls.2 ~ mob.c + sc.c + sc.c*mob.c + ls.1c
fit1 <- lm(m1, data = data)
summary(fit1)

# get confidence intervals 
confint(fit1) 

# get standardised regression coefficients
lm.beta(fit1)

# calculate simple slopes
simple_slopes(fit1)

# check model
autoplot(fit1, which = 1:6, ncol = 3, label.size = 3)

# model with covariates
# ----------------------------

# define and fit model
m2 <- ls.2 ~ mob.c + sc.c + sc_mob + ls.1c + age.c + sex + SESt1
fit2 <- lm(m2, data = data)
summary(fit2)

# get confidence intervals
confint(fit2) 

# get standardised regression coefficients
lm.beta(fit2)

# check model
autoplot(fit2, which = 1:6, ncol = 3, label.size = 3)

# ------------------------------
# Plots Moderated regression
# ------------------------------

psych::describe(data[c("sc", "mob")])

interact_plot(fit1, pred = mob.c, modx =sc.c, #partial.residuals = TRUE,
              interval = TRUE,
              int.width = 0.95,
              modx.values = c(-1.48, 0, 1.48), 
              colors = c("#D9ED92", "#52B69A", "#1E6091"), 
              modx.labels = c("Low (- 1SD)", "Middle (Mean)", "High (+ 1SD)"), 
              legend.main = "Perceived status loss") +
  labs(y = "Predicted life satisfaction", x = "Upward mobility beliefs") +
  guides(fill = guide_legend(title = "Perceived status loss")) +
  coord_cartesian(ylim = c(1,7)) +
  scale_y_continuous(expand = c(0, 0), breaks = c(1,2,3,4,5,6,7)) +
  scale_x_continuous(expand = c(0.05, 0.05), breaks = c(-2.94,-1.94, -0.94, 0.06, 1.06, 2.06, 3.06), 
                     labels = c(0,1,2,3,4,5,6)) +
  theme_classic(base_size = 15) +
  theme(
    axis.title = element_text(colour = "black", size = 19, margin = margin(t = 0, r = 15, b = 0, l = 0)),         
    axis.text.x  = element_text(colour = "black", size = 19, margin = margin(t = 15, r = 0, b = 0, l = 0)), 
    axis.text.y  = element_text(colour = "black", size = 19), 
    legend.position = c(0.7,0.85), 
    legend.title = element_text(size = 17),
    legend.text = element_text(size = 17), 
    legend.key.width = unit(1,"cm")
  ) +
  theme(panel.grid.major = element_blank(),
        panel.grid.minor = element_blank(),
        panel.background = element_blank())

# save plot
ggsave("plot2.pdf", width = 7, height = 6)


