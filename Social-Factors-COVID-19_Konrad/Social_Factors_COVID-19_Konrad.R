---
title: "Konrad et al. Social Factors during COVID-19 pandemic"
author: "Annika Konrad"
---

# install.packages(c("compareGroups", "psych", "lme4", "emmeans", 
#                    "robustlmm", "sjPlot", "performance", "ggeffects", 
#                    "ggplot2", "ggnewscale", "see"))

library(compareGroups)
library(psych)
library(lme4)
library(emmeans) # ! Version 1.5.5-1
library(robustlmm) # ! > Version 2.4
library(sjPlot)
library(performance)
library(ggeffects)
library(ggplot2)
library(ggnewscale)
library(see)

#### Load Dataframe and setwd()
# setwd("")
data_long <- read.csv2("data_Konrad_etal.csv")

####################################################################################
####################################################################################
### 1. Data Preparation
####################################################################################
# check string issues
data_long$id <- as.numeric(data_long$id)
data_long$id_measurements <- as.numeric(data_long$id_measurements)
data_long$age <- as.numeric(data_long$age)
data_long[,24:99] <- lapply(data_long[,24:99], as.numeric) # turn integers to numeric
data_long[, 5:16] <- lapply(data_long[,5:16], as.factor) 

# combine treatment setting
data_long$treatment_setting2 <- factor(ifelse(data_long$treatment_setting == "A1: No Psychotherapy", "No Psychotherapy",
                                              ifelse(data_long$treatment_setting == "A2: Subsequent Treatment", "Current Psychotherapy", "Other")))
summary(data_long$treatment_setting2)

# calculate combined score for contact and digital items if necessary
data_long$contact = (data_long$contact_family + data_long$contact_friend)/2
data_long$digital = (data_long$digital_family + data_long$digital_friend)/2

# subset for baseline survey
baseline <- subset(data_long, id_measurements == 1)


# get descriptive reports
descr_diag <- compareGroups(diagnosis ~ age + gender + bsi_gsi + tics_socialisolation +
                              rsa_socialresources + bes_disconnection + 
                              household + contact + 
                              digital + work_homeoffice + work_lossofwork + 
                              work_normal + work_morehours + work_shortwork + 
                              diagnosis_category + stat_treatment + 
                              treatment_setting2, method = c(age = NA, household = NA, 
                                                             bsi_gsi = NA, tics_socialisolation = NA,
                                                             rsa_socialresources = NA, bes_disconnection = NA, 
                                                             contact = NA, digital = NA), 
                            data = baseline)

descr_diag
createTable(descr_diag)

# Note in the no diagnosis group 10 individuals stated mental health issues (see variable diagnosis_category)
# Since they never received a official diagnosis, we conducted a sensitivity analysis (see in script below)


###################################
### Check Cronbach's alpha at T0
###################################
### Basic Empathy Scale: Subscale Empathic Disconnection
alpha_bes_disconnection <- psych::alpha(baseline[c("bes_01", "bes_07", "bes_08", "bes_13", "bes_18", "bes_19")])
alpha_bes_disconnection$total

### Triers Chronic Stress inventory: Subscale social isolation
alpha_tics_socialisolation <- psych::alpha(baseline[c("tics_11", "tics_29", "tics_34", "tics_42", "tics_51", "tics_56")])
alpha_tics_socialisolation$total

### Resilience scale for adults: subscale social resources
alpha_rsa_socialresources <- psych::alpha(baseline[c("rsa_05", "rsa_11", "rsa_17", "rsa_23", "rsa_28", "rsa_32", "rsa_33")])
alpha_rsa_socialresources$total

### Brief Symptom Inventory 53: Sumscore
alpha_bsi_gsi <- psych::alpha(baseline[c("bsi_01", "bsi_02", "bsi_03", "bsi_04", "bsi_05", "bsi_06", "bsi_07", 
                                 "bsi_08", "bsi_09", "bsi_10", "bsi_11", "bsi_12", "bsi_13", "bsi_14", 
                                 "bsi_15", "bsi_16", "bsi_17", "bsi_18", "bsi_19", "bsi_20", "bsi_21", 
                                 "bsi_22", "bsi_23", "bsi_24", "bsi_25", "bsi_26", "bsi_27", "bsi_28", 
                                 "bsi_29", "bsi_30", "bsi_31", "bsi_32", "bsi_33", "bsi_34", "bsi_35", 
                                 "bsi_36", "bsi_37", "bsi_38", "bsi_39", "bsi_40", "bsi_41", "bsi_42", 
                                 "bsi_43", "bsi_44", "bsi_45", "bsi_46", "bsi_47", "bsi_48", "bsi_49", 
                                 "bsi_50", "bsi_51", "bsi_52", "bsi_53")])
alpha_bsi_gsi$total

####################################################################################
####################################################################################
### MODEL 1
####################################################################################
# due to NAs in age variable (min-/max problems), subset of data_long with no missings
# otherwise comparison of model0 and model0_1 with anova function is not possible
# due to different sample sizes
data_long.out <- subset(data_long, age != "NA")

## 1. Null model
model0 = lmer(bsi_gsi ~ (1|id), 
                data = data_long.out)
summary(model0)

## 2. Null Model with covariates
model0.1 = lmer(bsi_gsi ~ age + gender + (1|id), 
                data = data_long.out)
summary(model0.1)

# Compare models
anova(model0, model0.1)

# refit model0_1 with df "data_long" to compare with other models
model0.1 = lmer(bsi_gsi ~ age + gender + (1|id), 
                data = data_long, 
                na.action = "na.omit")
summary(model0.1)

## 3. Model 1 without interaction effect
model1 = lmer(bsi_gsi ~ daycount + diagnosis + rsa_socialresources + age + gender + (1|id), 
                   data = data_long, 
                   na.action = "na.omit")
summary(model1)

## 4. Add interaction effect
model1_full = lmer(bsi_gsi ~ daycount*diagnosis*rsa_socialresources + age + gender + (1|id), 
                   data = data_long,
                   na.action = "na.omit")
summary(model1_full)

###################################
### Compare models 
## 1. Regarding relevance of fixed effects
# CAVE: models are refitted with ML instead REML to compare likelihoods
anova(model0.1, model1, model1_full) 

## 2. compare model indices (ICC, conditional and margina R˛)
tab_model(model0.1, model1, model1_full) 

###################################
### Check model assumptions
check_heteroscedasticity(model1_full)
check_normality(model1_full)
check_outliers(model1_full)
check_autocorrelation(model1_full)

###################################
### Refit robust model
model1_robust <- rlmer(bsi_gsi ~ daycount*diagnosis*rsa_socialresources + age + gender + (1|id), 
                   data = data_long,
                   na.action = "na.omit")
summary(model1_robust)

## Compare models
tab_model(model1_full, model1_robust, 
          show.se = TRUE, digits = 3, title = "Model Comparison")

###################################
### Plot robust model 1
## get predicted Values for different levels of rsa_socialresources
gg_model1 <- ggpredict(model1_robust, c("daycount[0, 25, 50, 75]", "rsa_socialresources[meansd]", "diagnosis"))

## Plot
plot(gg_model1) + 
  labs(title = "Time x Social Resources x Diagnosis", x = "Time [in days]", 
                     y= "Psychological Distress",
                     colour = "Social\nResources") +
  guides(colour = guide_legend(reverse = TRUE)) +
  scale_color_hue(labels = c("4.84 (-SD)", "5.77 (Mean)", "6.7 (+SD)")) + 
  scale_y_continuous(breaks = c(0, 0.4, 0.8, 1.2)) + ylim(0,1.2)

###################################
### Post tests for each group

## Diagnosis group
data_long.affected <- subset(data_long, diagnosis == "Diagnosis")

model1_affected <- rlmer(bsi_gsi ~ daycount*rsa_socialresources + age + gender + (1|id), 
                data = data_long.affected,
                na.action = "na.omit")
summary(model1_affected)

## No Diagnosis group
data_long.unaffected <- subset(data_long, diagnosis == "No Diagnosis")

model1_unaffected <- rlmer(bsi_gsi ~ daycount*rsa_socialresources + age + gender + (1|id), 
                data = data_long.unaffected,
                na.action = "na.omit")
summary(model1_unaffected)

## Compare models
tab_model(model1_affected, model1_unaffected, show.se = TRUE, 
          digits = 3, title = "Model Comparison", file = "model1_sep.html")

## Plot separate models
gg_m1_affected <- ggpredict(model1_affected, c("daycount", "rsa_socialresources[meansd]"))
plot(gg_m1_affected)

gg_m1_unaffected <- ggpredict(model1_unaffected, c("daycount", "rsa_socialresources[meansd]"))
plot(gg_m1_unaffected)

###################################
### Trend Analysis
## 1. Pairwise comparisons of slopes
emtrends_m1 <- emtrends(model1_robust, pairwise ~ rsa_socialresources*diagnosis, 
                         var = c("daycount"), at = list(rsa_socialresources=c(4.84, 5.77, 6.7)), adjust = "bonf")

tab_df(data.frame(emtrends_m1$emtrends), digits = 3, file = "emtrends1.html")

## 2. Marginal means
emmeans_m1 <- emmeans(model1_robust, pairwise ~ rsa_socialresources*diagnosis,
        at = list(rsa_socialresources=c(4.84, 5.77, 6.7)), adjust = "bonf")

tab_df(data.frame(emmeans_m1$contrasts), digits = 3, file = "emmeans1.html")

####################################################################################
####################################################################################
#### Model 2
####################################################################################

## 1. Model 2 without interaction effect
model2 = lmer(bsi_gsi ~ daycount + diagnosis + bes_disconnection + age + gender + (1|id), 
                data = data_long, 
                na.action = "na.omit")
summary(model2)

# 2. Add interaction effect
model2_full <- lmer(bsi_gsi ~ daycount*diagnosis*bes_disconnection + age + gender + (1|id), 
                    data = data_long,
                    na.action = "na.omit")
summary(model2_full)

###################################
### Compare models 
## 1. Regarding relevance of fixed effects
# CAVE: models are refitted with ML instead REML to compare likelihoods
anova(model0.1, model2, model2_full)

## 2. compare model indices (ICC, conditional and margina R˛)
tab_model(model0.1, model2, model2_full)

###################################
### Check model assumptions
check_heteroscedasticity(model2_full)
check_normality(model2_full)
check_outliers(model2_full)
check_autocorrelation(model2_full)

###################################
### Refit robust model
model2_robust <- rlmer(bsi_gsi ~ daycount*diagnosis*bes_disconnection + age + gender + (1 |id), 
              data = data_long,
              na.action = "na.omit")
summary(model2_robust)

## Compare model fit
tab_model(model2_full, model2_robust, 
          show.se = TRUE, digits = 3, title = "Model Comparison")


###################################
### Plot Model 2
# get estimates at fixed levels 
gg_model2 <- ggpredict(model2_robust, c("daycount[0, 25, 50, 75]", "bes_disconnection[meansd]", "diagnosis"))

plot(gg_model2) + 
  labs(title = "Time x Empathic Disconnection x Diagnosis", x = "Time [in days]", y= "Psychological Distress",
                     colour = "Empathic\nDisconnection") +
  guides(colour = guide_legend(reverse = TRUE)) +
  scale_color_hue(labels = c("1.57 (-SD)", "2.15 (Mean)", "2.73 (+SD)")) + ylim(0,1.2)

###################################
### Post tests for each group

## Diagnosis group
model2_affected <- rlmer(bsi_gsi ~ daycount*bes_disconnection + age + gender + (1 |id), 
                data = data_long.affected,
                na.action = "na.omit")
summary(model2_affected)

# No Diagnosis group
model2_unaffected <- rlmer(bsi_gsi ~ daycount*bes_disconnection + age + gender + (1 |id), 
                         data = data_long.unaffected,
                         na.action = "na.omit")
summary(model2_unaffected)

## Compare models
tab_model(model2_affected, model2_unaffected, 
          show.se = TRUE, digits = 3, title = "Model Comparison Per Group", file = "model2_sep.html")


## Plot separate models
gg_m2_affected <- ggpredict(model2_affected, c("daycount", "bes_disconnection[meansd]"))
plot(gg_m2_affected)

gg_m2_unaffected <- ggpredict(model2_unaffected, c("daycount", "bes_disconnection[meansd]"))
plot(gg_m2_unaffected)


###################################
### Trend Analysis
## 1. Pairwise comparison of slopes
emtrends_m2 <- emtrends(model2_robust, pairwise ~ bes_disconnection*diagnosis, 
                        var = c("daycount"), 
                        at = list(bes_disconnection=c(1.57, 2.15, 2.73)), 
                        adjust = "bonf")

tab_df(data.frame(emtrends_m2$emtrends), digits = 3, file = "emtrends2.html")

### 2. Marginal means
emmeans_m2 <- emmeans(model2_robust, pairwise ~ bes_disconnection*diagnosis,
                        at = list(bes_disconnection=c(1.57, 2.15, 2.73)), 
                      adjust = "bonf")

tab_df(data.frame(emmeans_m2$contrasts), digits = 3, file = "emmeans2.html")


####################################################################################
####################################################################################
### MODEL 3
####################################################################################

## 1. Model 3 with Only covariates
model0.2 <- lmer(bsi_gsi ~ age + gender + 
                      household + digital + contact + (1|id), 
                    data = data_long,
                    na.action = "na.omit")
summary(model0.2)

## 2. Model 3 without interaction effect
model3 <- lmer(bsi_gsi ~ daycount + diagnosis + tics_socialisolation + age + gender + 
                      household + digital + contact + (1|id), 
                    data = data_long,
                    na.action = "na.omit")
summary(model3)

## 3. Add interaction effect
model3_full <- lmer(bsi_gsi ~ daycount*diagnosis*tics_socialisolation + age + gender + 
                 household + digital + contact + (1|id), 
               data = data_long,
               na.action = "na.omit")
summary(model3_full)

###################################
### Compare models 
## 1. Regarding relevance of fixed effects
# CAVE: models are refitted with ML instead REML to compare likelihoods
anova(model0.2, model3, model3_full)

## 2. compare model indices (ICC, conditional and margina R˛)
tab_model(model0.2, model3, model3_full)

###################################
### Check model assumptions
check_heteroscedasticity(model3_full)
check_normality(model3_full)
check_outliers(model3_full)
check_autocorrelation(model3_full)

###################################
### Refit robust model
model3_robust <- rlmer(bsi_gsi ~ daycount*diagnosis*tics_socialisolation + 
                         age + gender + household + digital + contact + 
                         (1|id), 
                       data = data_long,
                       na.action = "na.omit")
summary(model3_robust)

## Compare models
tab_model(model3_full, model3_robust, 
          show.se = TRUE, digits = 3, title = "Model Comparison")

###################################
# Plot robust model 3
gg_model3 <- ggpredict(model3_robust, c("daycount[0, 25, 50, 75]", "tics_socialisolation[meansd]", "diagnosis"))

plot(gg_model3) + 
  labs(title = "Time x Social Isolation x Diagnosis", x = "Time [in days]", y= "Psychological Distress",
                     colour = "Social\nIsolation") + 
  guides(colour = guide_legend(reverse = TRUE)) +
  scale_color_hue(labels = c("0.53 (-SD)", "1.52 (Mean)", "2.51 (+SD)")) + 
  scale_y_continuous(breaks = seq(0, 1.2, by = 0.3)) + ylim(0,1.2)

###################################
### Post tests for each group

## Diagnosis group
model3_affected <- rlmer(bsi_gsi ~ daycount*tics_socialisolation + age + gender + household + 
                  digital + contact + (1 |id), 
                data = data_long.affected,
                na.action = "na.omit")
summary(model3_affected)

## No Diagnosis group
model3_unaffected <- rlmer(bsi_gsi ~ daycount*tics_socialisolation + age + gender + household + 
                           digital + contact + (1 |id), 
                         data = data_long.unaffected,
                         na.action = "na.omit")
summary(model3_unaffected)

## Compare models
tab_model(model3_affected, model3_unaffected, show.se = TRUE, digits = 3, 
          title = "Model Comparison Per Group", file = "model3_sep.html")

## Plot separate models
gg_m3_affected <- ggpredict(model3_affected, c("daycount", "tics_socialisolation[meansd]"))
plot(gg_m3_affected)

gg_m3_unaffected <- ggpredict(model3_unaffected, c("daycount", "tics_socialisolation[meansd]"))
plot(gg_m3_unaffected)

###################################
### Trend Analysis Model 3
## 1. Pairwise comparisons of slopes
emtrends_m3 <- emtrends(model3_robust, pairwise ~ tics_socialisolation*diagnosis, 
                        var = c("daycount"), 
                        at = list(tics_socialisolation=c(0.53, 1.52, 2.51)), adjust = "bonf")

tab_df(data.frame(emtrends_m3$emtrends), digits = 3, file = "emtrends3.html")

## 2. Marginal means
emmeans_m3 <- emmeans(model3_robust, pairwise ~ tics_socialisolation*diagnosis,
                        at = list(tics_socialisolation=c(0.53, 1.52, 2.51)), adjust = "bonf")

tab_df(data.frame(emmeans_m3$contrasts), digits = 3, file = "emmeans3.html")

####################################################################################
# summary all robust models
tab_model(model1_robust, model2_robust, model3_robust,  
          show.stat = TRUE, digits = 3, file = "Allrobustmodels.html")

####################################################################################
####################################################################################
# SENSITIVITY ANALYSIS
####################################################################################

data_long_noout <- subset(data_long, diagnosis != "No Diagnosis" | stat_treatment != "Yes") # exclude 7 individuals with 
data_long_outl <- subset(data_long, diagnosis == "No Diagnosis" & stat_treatment == "Yes")
View(data_long_outl)


###################################
### Robust model 1
model1_noout <- rlmer(bsi_gsi ~ daycount*diagnosis*rsa_socialresources + age + gender + (1|id), 
                      data = data_long_noout,
                      na.action = "na.omit")
summary(model1_noout)

tab_model(model1_robust, model1_noout, digits = 3, file = "model1_noout.html")

###################################
### Robust model 2
model2_noout <- rlmer(bsi_gsi ~ daycount*diagnosis*bes_disconnection + age + gender + (1 |id), 
                      data = data_long_noout,
                      na.action = "na.omit")
summary(model2_noout)

tab_model(model2_robust, model2_noout, digits = 3, file = "model2_noout.html")

###################################
### Robust model 3

# robust Model
model3_noout <- rlmer(bsi_gsi ~ daycount*diagnosis*tics_socialisolation + age + gender + household + 
                        digital + contact + (1 |id), 
                      data = data_long_noout,
                      na.action = "na.omit")
summary(model3_noout)

tab_model(model3_robust, model3_noout, digits = 3, file = "model3_noout.html")

####################################################################################
# 2ND SENSITIVITY ANALYSIS
####################################################################################
data_long_noout_curtreat <- subset(data_long, 
                                   diagnosis != "No Diagnosis" | treatment_setting2 != "Current Psychotherapy") # exclude 28 individuals with 
data_long_outl_curtreat <- subset(data_long, 
                                  diagnosis == "No Diagnosis" & treatment_setting2 == "Current Psychotherapy")

###################################
### Robust model 1
model1_noout_curtreat <- rlmer(bsi_gsi ~ daycount*diagnosis*rsa_socialresources + age + gender + (1|id), 
                               data = data_long_noout_curtreat,
                               na.action = "na.omit")
summary(model1_noout_curtreat)

tab_model(model1_robust, model1_noout_curtreat, digits = 3, file = "model1_noout_curtreat.html")

###################################
### Robust model 2
model2_noout_curtreat <- rlmer(bsi_gsi ~ daycount*diagnosis*bes_disconnection + age + gender + (1 |id), 
                               data = data_long_noout_curtreat,
                               na.action = "na.omit")
summary(model2_noout_curtreat)

tab_model(model2_robust, model2_noout_curtreat, digits = 3, file = "model2_noout_curtreat.html")

###################################
### Robust model 3
model3_noout_curtreat <- rlmer(bsi_gsi ~ daycount*diagnosis*tics_socialisolation + age + gender + household + 
                                 digital + contact + (1 |id), 
                               data = data_long_noout_curtreat,
                               na.action = "na.omit")
summary(model3_noout_curtreat)
tab_model(model3_robust, model3_noout_curtreat, digits = 3, file = "model3_noout_curtreat.html")

####################################################################################
# 3RD SENSITIVITY ANALYSIS
####################################################################################
data_long_noout_diagcat <- subset(data_long, diagnosis != "No Diagnosis" | is.na(data_long$diagnosis_category)) # exclude 44 obs. 
data_long_outl_diagcat <- subset(data_long, diagnosis == "No Diagnosis" & diagnosis_category != "NA")


###################################
### Robust model 1
model1_noout_diagcat <- rlmer(bsi_gsi ~ daycount*diagnosis*rsa_socialresources + age + gender + (1|id), 
                              data = data_long_noout_diagcat,
                              na.action = "na.omit")
summary(model1_noout_diagcat)

tab_model(model1_robust, model1_noout_diagcat, digits = 3, file = "model1_noout_diagcat.html")

###################################
### Robust model 2
model2_noout_diagcat <- rlmer(bsi_gsi ~ daycount*diagnosis*bes_disconnection + age + gender + (1 |id), 
                              data = data_long_noout_diagcat,
                              na.action = "na.omit")
summary(model2_noout_diagcat)

tab_model(model2_robust, model2_noout_diagcat, digits = 3, file = "model2_noout_diagcat.html")

###################################
### Robust model 3
model3_noout_diagcat <- rlmer(bsi_gsi ~ daycount*diagnosis*tics_socialisolation + age + gender + household + 
                                digital + contact + (1 |id), 
                              data = data_long_noout_diagcat,
                              na.action = "na.omit")
summary(model3_noout_diagcat)
tab_model(model3_robust, model3_noout_diagcat, digits = 3, file = "model3_noout_diagcat.html")
