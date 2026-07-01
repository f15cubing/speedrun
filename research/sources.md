# Consolidated Bibliography — GRE Speedrun Research

_Consolidated from sub-agent responses; confidence/quality assessments live in the per-response critiques (`research/critiques/`) and `research/SYNTHESIS.md`._

_Deduplicated across the 16 stored responses (`research/responses/01`–`07`, `01b`, `08`–`15`). Each entry notes which prompt(s) cited it, e.g. `[cited in: 02, 03]`. Flags: `[SUPERSEDED]` = a newer edition replaces it; `[contested]` / `[unofficial]` / `[erroneous]` = reliability caveat carried from the responses; `[replication-failed]` / `[small-sample]` / `[verify]` = robustness caveat from Rounds 3–4; `[vendor]` / `[practitioner]` = non-peer-reviewed source type._

---

## 1. Peer-reviewed papers & meta-analyses (incl. arXiv research preprints)

### Memory, calibration, cognitive science
- Ye, J., Su, Y., & Cao, Y. (2022). *A Stochastic Shortest Path Algorithm for Optimizing Spaced Repetition Scheduling* (SSP-MMC). KDD '22, 4381–4390. doi:10.1145/3534678.3539081 — peer-reviewed origin of the DHP/FSRS lineage. [cited in: 02]
- Brier, G. W. (1950). *Verification of Forecasts Expressed in Terms of Probability.* Monthly Weather Review 78:1–3. doi:10.1175/1520-0493(1950)078<0001:VOFEIT>2.0.CO;2 [cited in: 02]
- DeGroot, M. H., & Fienberg, S. E. (1983). *The comparison and evaluation of forecasters.* (Calibration / reliability diagrams.) [cited in: 02]
- Guo, C., Pleiss, G., Sun, Y., & Weinberger, K. Q. (2017). *On Calibration of Modern Neural Networks.* ICML. [cited in: 02]
- Naeini, M. P., Cooper, G., & Hauskrecht, M. (2015). *Obtaining Well Calibrated Probabilities Using Bayesian Binning (BBQ).* AAAI. [cited in: 02]
- Morris, C. D., Bransford, J. D., & Franks, J. J. (1977). *Levels of processing versus transfer appropriate processing.* J. Verbal Learning & Verbal Behavior 16:519–533. [cited in: 02]
- Barnett, S. M., & Ceci, S. J. (2002). *When and where do we apply what we learn? A taxonomy for far transfer.* Psychological Bulletin 128(4):612–637. doi:10.1037/0033-2909.128.4.612 [cited in: 02, 09]
- Roediger, H. L., & Karpicke, J. D. (2006). *The Power of Testing Memory* (Perspectives on Psych. Science 1:181–210) and *Test-Enhanced Learning* (Psychological Science 17:249–255). [cited in: 02]
- Rowland, C. A. (2014). *The effect of testing versus restudy on retention: a meta-analytic review.* Psychological Bulletin 140(6):1432–1463 (g≈0.50). [cited in: 02, 04]
- Adesope, O. O., Trevisan, D. A., & Sundararajan, N. (2017). *Rethinking the Use of Tests: A Meta-Analysis of Practice Testing.* Review of Educational Research 87(3):659–701. doi:10.3102/0034654316689306 (g=0.61). [cited in: 02, 04]
- Pan, S. C., & Rickard, T. C. (2018). *Transfer of Test-Enhanced Learning: Meta-Analytic Review and Synthesis.* Psychological Bulletin 144(7):710–756 (transfer d≈0.40; format-match d=0.58). [cited in: 02, 04, 10, 15]

### Psychometrics, statistics, ML calibration/leakage (performance/readiness/eval)
- McNemar, Q. (1947). *Note on the sampling error of the difference between correlated proportions or percentages.* Psychometrika 12(2):153–157. [cited in: 03]
- Murphy, A. H. (1973). *A new vector partition of the probability score* (Brier decomposition: reliability+resolution+uncertainty). [cited in: 03]
- Platt, J. (1999). *Probabilistic outputs for SVMs* (Platt scaling). [cited in: 03]
- Zadrozny, B., & Elkan, C. (2001/2002). *Calibration / isotonic regression for probability estimates.* [cited in: 03]
- Broder, A. (1997). *On the resemblance and containment of documents* (MinHash). [cited in: 03]
- Indyk, P., & Motwani, R. (1998). *Approximate nearest neighbors* (LSH). [cited in: 03]
- Angelopoulos, A. N., & Bates, S. (2021). *A Gentle Introduction to Conformal Prediction.* [cited in: 03]
- Kapoor, S., & Narayanan, A. (2023). *Leakage and the reproducibility crisis in ML-based science.* Patterns 4(9):100804. doi:10.1016/j.patter.2023.100804 (earlier preprint arXiv:2207.07048). [cited in: 03, 07, 11]
- Fagerland, M. W., Lydersen, S., & Laake, P. (2013). *The McNemar test for binary matched-pairs data: mid-p and asymptotic are better than exact conditional.* BMC Med Res Methodol 13:91. [cited in: 03, 11]
- Haladyna, T. M., Downing, S. M., & Rodriguez, M. C. (2002). *A Review of Multiple-Choice Item-Writing Guidelines.* Applied Measurement in Education 15(3):309–334. [cited in: 11]
- Wilson, E. B. (1927). *Probable inference, the law of succession, and statistical inference* (Wilson score interval). JASA 22:209–212. [cited in: 11]
- Taube, K. T. (1997). *The Incorporation of Empirical Item Difficulty Data into the Angoff Standard-Setting Procedure.* Evaluation & the Health Professions 20(4):479–498. [cited in: 11]

### Learning science (study feature / ablation / olympiad risk)
- Brunmair, M., & Richter, T. (2019). *Similarity Matters: A Meta-Analysis of Interleaved Learning and Its Moderators.* Psychological Bulletin 145(11):1029–1052 (overall g=0.42; math g=0.34). [cited in: 04, 10]
- Rohrer, D., Dedrick, R. F., Hartwig, M. K., & Cheung, C.-N. (2020). *A randomized controlled trial of interleaved mathematics practice.* J. Educational Psychology 112(1):40–52 (d=0.83). [cited in: 04]
- Rohrer, D., Dedrick, R. F., & Stershic, S. (2015). *Interleaved Practice Improves Mathematics Learning.* J. Educational Psychology 107(3):900–908. [cited in: 10]
- Cepeda, N. J., Pashler, H., Vul, E., Wixted, J. T., & Rohrer, D. (2006). *Distributed practice in verbal recall tasks: A review and quantitative synthesis.* Psychological Bulletin 132(3):354–380. [cited in: 04]
- Mawson & Kang (2025). *The Distributed Practice Effect on Classroom Learning.* Behavioral Sciences 15(6):771 (d=0.54). [cited in: 04]
- Barbieri, C. A., Miller-Cotto, D., Clerjuste, S. N., & Chawla, K. (2023). *A Meta-Analysis of Worked Examples in Mathematics.* Educational Psychology Review 35:11 (g=0.48). [cited in: 04]
- Sweller, J., & Cooper, G. A. (1985). *The use of worked examples as a substitute for problem solving.* [cited in: 04]
- Wittwer, J., & Renkl, A. (2010). *How effective are instructional explanations in example-based learning?* (near/far transfer not sig. different from zero). [cited in: 04]
- Shute, V. J. (2008). *Focus on Formative Feedback.* Review of Educational Research 78(1):153–189. [cited in: 04]
- Ryan et al. (2024). RCT on immediate vs delayed feedback. *Medical Education.* [cited in: 04]
- Faul, F., Erdfelder, E., Lang, A.-G., & Buchner, A. (2007). *G*Power 3.* [cited in: 04]
- Lakens, D. (2017). *Equivalence tests (TOST).* Social Psychological and Personality Science 8(4):355–362. doi:10.1177/1948550617697177 [cited in: 04, 14, 15]
- Lakens, D., Scheel, A. M., & Isager, P. M. (2018). *Equivalence testing for psychological research.* AMPPS. [cited in: 04]
- Sweller, J. (1988). *Cognitive Load During Problem Solving: Effects on Learning.* Cognitive Science 12(2):257–285. [cited in: 09, 10]
- Kalyuga, S., Ayres, P., Chandler, P., & Sweller, J. (2003). *The Expertise Reversal Effect.* Educational Psychologist 38(1):23–31. [cited in: 10]
- Kalyuga, S. (2007). *Expertise Reversal Effect and Its Implications for Learner-Tailored Instruction.* Educational Psychology Review 19:509–539. [cited in: 10]
- Macnamara, B. N., Hambrick, D. Z., & Oswald, F. L. (2014). *Deliberate Practice and Performance…: A Meta-Analysis.* Psychological Science 25(8):1608–1618. [cited in: 10]
- Macnamara, B. N., Hambrick, D. Z., & Moreau, D. (2016). *How Important Is Deliberate Practice? Reply to Ericsson (2016).* Perspectives on Psychological Science 11(3):333–350. [cited in: 10]
- Hambrick, D. Z., Macnamara, B. N., & Oswald, F. L. (2020). *Is the Deliberate Practice View Defensible?* Frontiers in Psychology 11:1134. [cited in: 10]
- Wilson, R. C., Shenhav, A., Straccia, M., & Cohen, J. D. (2019). *The Eighty Five Percent Rule for Optimal Learning.* Nature Communications 10:4646. (analogical to test prep). [cited in: 10]
- Murray, Horner & Göbel (2025). *A Meta-Analytic Review of Spacing and Retrieval Practice for Mathematics Learning.* Educational Psychology Review 37:75 (spacing math g=0.28; testing math g=0.18, CI crosses 0). [cited in: 10]

### Transfer of training & cognitive-training (olympiad thread)
- Thorndike, E. L., & Woodworth, R. S. (1901). *The influence of improvement in one mental function upon the efficiency of other functions* (identical elements). Psychological Review. [cited in: 09]
- Salomon, G., & Perkins, D. N. (1989). *Rocky roads to transfer.* Educational Psychologist 24(2):113–142 (low-road/high-road; also Perkins & Salomon 1992). [cited in: 09]
- Simons, D. J., et al. (2016). *Do "Brain-Training" Programs Work?* Psychological Science in the Public Interest 17(3):103–186. [cited in: 09]
- Owen, A. M., et al. (2010). *Putting brain training to the test.* Nature 465(7299):775–778. [cited in: 09]
- Sala, G., & Gobet, F. (2017). *Does far transfer exist? Negative evidence from chess, music, and working memory training.* Current Directions in Psychological Science 26(6):515–520. [cited in: 09]
- Sala, G., et al. (2019). *Near and far transfer in cognitive training: A second-order meta-analysis.* J. of Cognition / Collabra: Psychology. [cited in: 09]
- Saunders, T., Driskell, J. E., Johnston, J. H., & Salas, E. (1996). *The effect of stress inoculation training on anxiety and performance.* J. Occupational Health Psychology 1(2):170–186. [cited in: 09]
- Rebholz, F., Golle, J., Tibus, M., Ruth-Herbein, E., Moeller, K., & Trautwein, U. (2022). *Getting fit for the Mathematical Olympiad…* Zeitschrift für Erziehungswissenschaft 25(5):1175–1198. (the single most relevant controlled study; quasi-experimental, N=201 children). [cited in: 09]
- Solomon, T., et al. (2019). *A cluster RCT of the impact of the JUMP Math program.* PLOS ONE 14(10):e0223049. [cited in: 09]
- Wai, J., Lubinski, D., Benbow, C. P., & Steiger, J. H. (2010). *Accomplishment in STEM and its relation to STEM educational dose.* J. Educational Psychology 102(4):860–871. [cited in: 09]
- Lubinski, D., & Benbow, C. P. (2006). *Study of Mathematically Precocious Youth after 35 years.* Perspectives on Psychological Science 1(4):316–345. [cited in: 09]
- ZDM – Mathematics Education (2022). *Perspectives on mathematics competitions and their relationship with mathematics education.* doi:10.1007/s11858-022-01404-z [cited in: 08]
- Davison et al. (2012); Lu, Y., & Sireci, S. G. (2007). *Validity Issues in Test Speededness* (speed as a separable latent factor). [cited in: 08]

### AI evaluation / LLM math reliability (AI card generation)
- Petrov et al. (2025). *Proof or Bluff? Evaluating LLMs on 2025 USA Math Olympiad.* arXiv:2503.21934 (answer-only vs proof construct gap). [cited in: 08]
- Rashkin, H., et al. (2023). *Measuring Attribution in Natural Language Generation Models* (AIS). Computational Linguistics/TACL. [cited in: 07]
- Slobodkin, A., et al. (2024). *Attribute First, then Generate.* arXiv. [cited in: 07]
- Gao, T., Yen, H., Yu, J., & Chen, D. (2023). *Enabling LLMs to Generate Text with Citations* (ALCE). EMNLP. [cited in: 07]
- Gao, L., et al. (2023). *RARR: Researching and Revising What Language Models Say.* ACL. [cited in: 07]
- Kirichenko, P., et al. (2025). *AbstentionBench.* FAIR/Meta, arXiv. [cited in: 07]
- Song et al. (2024). *TRUST-SCORE / Learning to Refuse.* arXiv. [cited in: 07]
- Cobbe, K., et al. (2021). *Training Verifiers to Solve Math Word Problems* (GSM8K). arXiv:2110.14168 (<2% human-curation error). [cited in: 07]
- Glazer, E., et al. (2024). *FrontierMath* (SymPy verification). [cited in: 07]
- Gao, L., et al. (2023). *PAL: Program-aided Language Models.* ICML, arXiv:2211.10435 (GSM-Hard 61.2% vs CoT 23.3%). [cited in: 07]
- Lightman, H., et al. (2023). *Let's Verify Step by Step.* arXiv:2305.20050 (process supervision 78.2% on MATH subset). [cited in: 07]
- Wang, X., et al. (2022/2023). *Self-Consistency Improves Chain of Thought Reasoning.* arXiv:2203.11171 (GSM8K +17.9%). [cited in: 07]
- Es, S., et al. (2023). *RAGAS: Automated Evaluation of RAG.* EACL (faithfulness metric). [cited in: 07]
- Huang, J., et al. (2024). *Large Language Models Cannot Self-Correct Reasoning Yet.* [cited in: 07]
- Laban, P., et al. (2024). *FlipFlop experiment* ("Are you sure?" degrades accuracy). arXiv:2311.08596. [cited in: 07]
- Mirzadeh, I., et al. (Apple, 2024). *GSM-Symbolic.* arXiv:2410.05229 (up to 65% drop from irrelevant clause). [cited in: 07]
- Dietterich, T. G. (1998). *Approximate Statistical Tests for Comparing Supervised Classification Learning Algorithms* (McNemar for two systems). [cited in: 07]
- Wongpakaran, N., et al. (2013). *Gwet's AC1 vs Cohen's/Fleiss' kappa.* BMC Med Res Methodol. [cited in: 07]
- Yang, S., Chiang, W.-L., Zheng, L., Gonzalez, J. E., & Stoica, I. (2023). *Rethinking Benchmark and Contamination for Language Models with Rephrased Samples.* arXiv:2311.04850 (rephrased test sets evade n-gram detection). [cited in: 03, 07, 11]
- Brown, T., et al. (2020). *Language Models are Few-Shot Learners* (GPT-3; 13-gram contamination check). [cited in: 03, 07]
- Touvron, H., et al. (2023). *Llama-2* (n-gram contamination methodology). [cited in: 03]
- OpenAI (2023). *GPT-4 Technical Report* (50-char overlap contamination signal). [cited in: 07]
- LECTOR (Zhao, 2025). arXiv:2508.03275 — `[contested]` simulation-only, no calibration metrics, AI-authored/reviewed venue (Agents4Science 2025); does NOT independently validate FSRS. [cited in: 02]

### Test anxiety, stress-inoculation & interventions (Round 3 — anxiety thread)
*Meta-analyses & reviews*
- Hembree, R. (1988). *Correlates, Causes, Effects, and Treatment of Test Anxiety.* Review of Educational Research 58(1):47–77. doi:10.3102/00346543058001047 (562 studies; high-TA ≈ 0.5 SD below; treatment d≈0.42). [cited in: 12, 13, 14]
- Hembree, R. (1990). *The Nature, Effects, and Relief of Mathematics Anxiety.* J. for Research in Mathematics Education 21(1):33–46. doi:10.2307/749455 [cited in: 12]
- von der Embse, N., Jester, D., Roy, D., & Post, J. (2018). *Test anxiety effects, predictors, and correlates: A 30-year meta-analytic review* (238 studies). J. of Affective Disorders 227:483–493. doi:10.1016/j.jad.2017.11.048 (standardized-test r≈−.26; worry > emotionality). [cited in: 12, 13, 14]
- Barroso, C., Ganley, C. M., et al. (2021). *A meta-analysis of the relation between math anxiety and math achievement* (223 studies). Psychological Bulletin 147(2):134–168. doi:10.1037/bul0000307 (r≈−.28; publication bias detected; smaller r in low-ability samples). [cited in: 12]
- Ergene, T. (2003). *Effective interventions on test anxiety reduction: A meta-analysis* (56 studies). School Psychology International 24(3):313–328. doi:10.1177/01430343030243004 (anxiety E++=0.65 [0.58–0.73]; performance NOT measured). [cited in: 12, 14]
- Huntley, C. D., Young, B., et al. (2019). *The efficacy of interventions for test-anxious university students: A meta-analysis of RCTs* (44 RCTs). J. of Anxiety Disorders 63:36–50. doi:10.1016/j.janxdis.2019.01.007 (anxiety g=−0.76→−0.64; **performance g=0.37→0.28** outliers removed; publication bias). [cited in: 12, 13, 14]
- Saunders, T., Driskell, J. E., Johnston, J. H., & Salas, E. (1996). *The effect of stress inoculation training on anxiety and performance.* J. Occupational Health Psychology 1(2):170–186. doi:10.1037/1076-8998.1.2.170 (performance r≈.296; .352 for high-anxiety). [cited in: 09, 13]
- Bosshard, M., & Gomez, P. (2024). *Effectiveness of stress arousal reappraisal and stress-is-enhancing mindset interventions on task performance: a meta-analysis of RCTs* (k=44). Scientific Reports 14:7923. doi:10.1038/s41598-024-58408-w (**d=0.23 overall**; publication bias flagged). `[verify — recent]` [cited in: 13]
- Manzoni, G. M., et al. (2008). *Relaxation training for anxiety: a ten-years systematic review with meta-analysis* (27 studies). BMC Psychiatry 8:41 (between-group d=0.51; online weaker). [cited in: 13]
- Behnke, M., & Kaczmarek, L. D. (2018). *Successful performance and cardiovascular markers of challenge and threat: A meta-analysis.* Int. J. of Psychophysiology (challenge/threat; publication-bias flag). [cited in: 13]
- Seipp, B. (1991). *Anxiety and academic performance: A meta-analysis.* Anxiety Research 4:27–41 (worry r≈−.30). [cited in: 12]
- von der Embse, N., Barterian, J., & Segool, N. (2013). *Test anxiety interventions for children and adolescents: a systematic review 2000–2010.* Psychology in the Schools 50(1):57–71. [cited in: 12]
- Korhonen / Caviola et al. (2021). *Working Memory and Its Mediating Role on Math Anxiety↔Math Performance: A Meta-Analysis* (57 studies). Frontiers in Psychology 12:798090 (direct r=−.168; WM indirect ≈−.09). `[author attribution uncertain — verify]` [cited in: 12]
- Caviola, S., et al. (2021). *Math Performance and Academic Anxiety Forms: A Meta-analysis* (~906,311 participants). Educational Psychology Review. doi:10.1007/s10648-021-09618-5 `[figure/scope — verify]` [cited in: 12]
- Mindfulness meta-analysis (attention/executive/WM). Cognitive Therapy and Research (2020). doi:10.1007/s10608-020-10177-2 [cited in: 13]

*Primary studies & replications (objective-score / real exam)*
- Jamieson, J. P., Mendes, W. B., Blackstock, E., & Schmader, T. (2010). *Turning the knots in your stomach into bows: Reappraising arousal improves performance on the GRE.* J. of Experimental Social Psychology 46(1):208–212. doi:10.1016/j.jesp.2009.08.015 `[small-sample N≈28; meta-analytic d≈0.23]` [cited in: 12, 13, 14]
- Jamieson, J. P., Peters, B. J., Greenwood, E. J., & Altose, A. J. (2016). *Reappraising Stress Arousal Improves Performance and Reduces Evaluation Anxiety in Classroom Exam Situations.* Social Psychological and Personality Science 7(6):579–587. doi:10.1177/1948550616644656 (community-college math, d≈0.53). [cited in: 12, 13, 14]
- Jamieson, J. P., Black, A. E., Pelaia, L. E., & Gravelding, H. (2022). *Reappraising stress arousal improves affective, neuroendocrine, and academic performance outcomes in community college classrooms.* J. of Experimental Psychology: General. doi:10.1037/xge0000893 [cited in: 13]
- Ramirez, G., & Beilock, S. L. (2011). *Writing About Testing Worries Boosts Exam Performance in the Classroom.* Science 331(6014):211–213. doi:10.1126/science.1199427 `[replication-failed: Camerer et al. 2018; original d≈2.48 implausibly large]` [cited in: 12, 13, 14]
- Camerer, C. F., et al. (2018). *Evaluating the replicability of social science experiments in Nature and Science between 2010 and 2015.* Nature Human Behaviour 2(9):637–644. doi:10.1038/s41562-018-0399-z (replications ≈50% of original effect; R&B 2011 failed). [cited in: 13, 14]
- Thormodsæter, R., Ballen, C., et al. (2026). *Can we mitigate the impacts of test anxiety through reappraisal interventions? A replication study in science courses across multiple institution types in the US.* CBE—Life Sciences Education 25(1):ar9. doi:10.1187/cbe.25-04-0055 (**null on anxiety AND performance; no moderation**; 12 courses / 7 institutions). `[verify — very recent, load-bearing]` [cited in: 14]
- Mrazek, M. D., Franklin, M. S., Phillips, D. T., Baird, B., & Schooler, J. W. (2013). *Mindfulness training improves working memory capacity and GRE performance while reducing mind wandering.* Psychological Science 24(5):776–781. doi:10.1177/0956797612459659 (2-wk course; ≈16-pct GRE-reading boost; brief versions null). [cited in: 13]
- Ashcraft, M. H., & Kirk, E. P. (2001). *The relationships among working memory, math anxiety, and performance.* J. of Experimental Psychology: General 130(2):224–237 (dual-task interference; up to 40% vs ~20% errors). [cited in: 12]
- Beilock, S. L., & Carr, T. H. (2005). *When high-powered people fail: Working memory and "choking under pressure" in math.* Psychological Science 16(2):101–105 (choking concentrates in high-WM individuals). [cited in: 12, 13]
- Cassady, J. C., & Johnson, R. E. (2002). *Cognitive Test Anxiety and Academic Performance.* Contemporary Educational Psychology 27(2):270–295. doi:10.1006/ceps.2001.1094 (Cognitive Test Anxiety Scale; cognitive facet most predictive). [cited in: 12, 14]
- Ramirez, G., Chang, H., Maloney, E. A., Levine, S. C., & Beilock, S. L. (2016). *On the relationship between math anxiety and math achievement in early elementary school.* J. of Experimental Child Psychology 141:83–100. [cited in: 12]
- Ramirez, G., Gunderson, E. A., Levine, S. C., & Beilock, S. L. (2013). *Math Anxiety, Working Memory, and Math Achievement in Early Elementary School.* J. of Cognition and Development 14(2):187–202. [cited in: 12]
- Ma, X., & Xu, J. (2004). *The causal ordering of mathematics anxiety and mathematics achievement: a longitudinal panel analysis.* J. of Adolescence. doi:10.1016/S0140-1971(03)00106-4 (cross-lagged; deficit/reciprocal lean). [cited in: 12]
- Myers, S. J., et al. *Does expressive writing or an instructional intervention reduce the impacts of test anxiety in a college classroom?* (4 authentic exams; null on anxiety and performance). [cited in: 12]
- Ginty, A. T., Oosterhoff, B. J., Young, D. A., & Williams, S. E. (2022). *Effects of arousal reappraisal on the anxiety responses to stress.* British J. of Psychology 113:131–152. doi:10.1111/bjop.12528 [cited in: 13]
- Liebert, R. M., & Morris, L. W. (1967). *Cognitive and emotional components of test anxiety.* Psychological Reports 20:975–978 (worry vs emotionality distinction). [cited in: 12]
- Gunderson et al. (2018); Cargnelutti et al. (2017); Sorvo et al. (2022) — longitudinal/cross-lagged math anxiety↔achievement studies. [cited in: 12]

*Mechanism / theory*
- Eysenck, M. W., Derakshan, N., Santos, R., & Calvo, M. G. (2007). *Anxiety and Cognitive Performance: Attentional Control Theory.* Emotion 7(2):336–353 (anxiety impairs processing efficiency > effectiveness). [cited in: 12, 13]
- Blascovich, J., & Mendes, W. B. (2010). *Social psychophysiology and embodiment.* In Handbook of Social Psychology (5th ed.) (challenge-vs-threat / biopsychosocial model). [cited in: 13]
- Meichenbaum, D. H., & Deffenbacher, J. L. (1988). *Stress inoculation training.* The Counseling Psychologist 16(1):69–90. doi:10.1177/0011000088161005 (3-phase SIT; application/graded-exposure phase). [cited in: 13, 14]

### Test-taking UI, computer-based testing & interface effects (Round 4 — testing-UI thread)
*Mode effects & CBT interface (objective-score/latency)*
- Wang, S., Jiao, H., Young, M. J., Brooks, T., & Olson, J. (2007). *A Meta-Analysis of Testing Mode Effects in Grade K–12 Mathematics Tests.* Educational and Psychological Measurement 67(2):219–238. doi:10.1177/0013164406288166 (no significant computer-vs-paper math effect; larger for linear than adaptive tests). [cited in: 15]
- Mead, A. D., & Drasgow, F. (1993). *Equivalence of computerized and paper-and-pencil cognitive ability tests: A meta-analysis.* Psychological Bulletin 114(3):449–458. (159 corrected correlations; cross-mode r≈.97 for power vs .72 for speeded tests — key for speeded GRE Math). [cited in: 15]
- Bridgeman, B., Lennon, M. L., & Jackenthal, A. (2003). *Effects of Screen Size, Screen Resolution, and Display Rate on Computer-Based Test Performance.* Applied Measurement in Education 16(3):191–205. doi:10.1207/S15324818AME1603_2 (n=357; smaller screens hurt reading ~¼ SD, **not math**). [cited in: 15]
- He, J. (2024). *The impact of clock timing on VDT visual search performance under time constraint.* Frontiers in Psychology 15:1369920. doi:10.3389/fpsyg.2024.1369920 (visible clock → faster RT, no accuracy change). `[small-sample n=21; verify]` [cited in: 15]
- Hallez, Q., & Vallier, V. (2025). *Time on Their Side: How Visual Timers Affect Anticipatory Anxiety, Performance, and On-Task Behavior in Elementary Math Assessments.* EJIHPE 15(12):243. doi:10.3390/ejihpe15120243 (visible timer ↓ anticipatory anxiety, no performance change). `[children n=44; verify]` [cited in: 15]

*Item review / answer change (objective-score)*
- van der Linden, W. J., Jeon, M., & Ferrara, S. (2011). *A Paradox in the Study of the Benefits of Test-Item Review.* Journal of Educational Measurement 48(4):380–398 (with erratum). doi:10.1111/j.1745-3984.2011.00151.x (argued review causes "substantial losses"; empirical basis withdrawn via erratum — model non-convergence). `[verify — erratum is load-bearing]` [cited in: 15]
- Bridgeman, B. (2012). *A Simple Answer to a Simple Question on Changing Answers.* Journal of Educational Measurement 49(4):467–468. doi:10.1111/j.1745-3984.2012.00189.x (overwhelming majority improve after changing answers). [cited in: 15]
- Liu, O. L., Bridgeman, B., Gu, L., Xu, J., & Kong, N. (2015). *Investigation of Response Changes in the GRE Revised General Test.* Educational and Psychological Measurement 75(6):1002–1020. (n≈8,538 Quant / 9,140 Verbal; net benefit that increases with ability). https://pmc.ncbi.nlm.nih.gov/articles/PMC5965601/ [cited in: 15]

*Feedback timing & cognitive load*
- Van der Kleij, F. M., Feskens, R. C. W., & Eggen, T. J. H. M. (2015). *Effects of Feedback in a Computer-Based Learning Environment on Students' Learning Outcomes: A Meta-Analysis.* Review of Educational Research 85(4):475–511. (elaborated feedback g=0.49 > KR 0.05 / KCR 0.32). [cited in: 15]
- Kulik, J. A., & Kulik, C.-L. C. (1988). *Timing of Feedback and Verbal Learning.* Review of Educational Research 58:79–97. [cited in: 15]
- Chandler, P., & Sweller, J. (1992). *The split-attention effect as a factor in the design of instruction.* British Journal of Educational Psychology 62:233–246. doi:10.1111/j.2044-8279.1992.tb01017.x (extraneous load from split attention — chrome/navigator grids). [cited in: 15]

*Novelty effect & time pressure*
- Rodrigues, L., Toda, A. M., Oliveira, W., Palomino, P. T., Avila-Santos, A. P., & Isotani, S. (2022). *Gamification suffers from the novelty effect but benefits from the familiarization effect.* International Journal of Educational Technology in Higher Education 19. https://link.springer.com/article/10.1186/s41239-021-00314-6 (N=756, 14-wk; novelty acts ~wk 4, lasts 2–6 wk, U-shaped). `[verify — figures]` [cited in: 15]
- "Should Intelligence Tests Be Speeded or Unspeeded?" (2023). PMC10299616 (Raven's; time pressure d≈0.35 accuracy decrement, concentrated in high-ability/WM examinees). https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10299616/ `[verify]` [cited in: 15]

---

## 2. Institutional / standards bodies

- **ETS** — *Practice Book for the GRE® Subject Test in Mathematics*, Form GR3768 (© 2024). Score Conversion Table p. 35 (60→880, 57–58→860; form ceiling 970). https://www.ets.org/pdfs/gre/practice-book-math.pdf [cited in: 01, 01b, 08, 10, 11]
- **ETS** — *GRE Subject Test Content and Structure* (blueprint: ~66 items; Calculus ~50%, Algebra ~25%, Additional ~25%; rights-only; 2h50m; computer-delivered since Sept 2023; scaled 200–990). https://www.ets.org/gre/test-takers/subject-tests/about/content-structure.html [cited in: 01, 08, 09, 10, 11, 15]
- **ETS** — *GRE Subject Test Interpretative Data*, Tables 2A/2B, **© 2025** (cohort July 2021–June 2024; Mathematics N=5,180, mean 680, SD 161; 880→88th, 800→71st). https://www.ets.org/pdfs/gre/gre-guide-table-2.pdf — **current edition.** [cited in: 01b, 03, 10]
- **ETS** — *GRE Subject Test Interpretive Data*, **© 2024** edition (cohort July 2019–June 2023; Mathematics N=7,452, mean 676, SD 154; 880→90th). `[SUPERSEDED]` by the © 2025 edition. [cited in: 01]
- **ETS** — *Interpreting Your GRE® Scores: 2024 and 2025–26* (Subject Test "Table 3"). https://www.ets.org/pdfs/gre/interpreting-gre-scores.pdf [cited in: 01b]
- **ETS** — *Understanding Your GRE Subject Test Scores* (equating language: no public number-correct→scaled table). https://www.ets.org/gre/test-takers/subject-tests/scores/understand-scores.html [cited in: 01b, 03]
- **ETS** — *GRE Subject Test to be Computer Delivered* (Sept 2023 online move). https://www.ets.org/gre/score-users/subject-test-changes.html [cited in: 01b]
- **ETS** — *Strategies & Tips for the GRE Subject Tests.* https://www.ets.org/gre/test-takers/subject-tests/prepare/strategies-tips.html [cited in: 08, 10]
- **ETS** — *Licensing/Permissions Policies* (no web-posting of items; ≤½ of a Subject Test). https://www.ets.org/legal/permissions/licensing.html [cited in: 11]
- **ETS** — older released Math forms with own conversion tables: GR1768/GR1268 (ceiling 910), GR0568 (900), GR9768/GR9767 (890, © 2001 rescaled), GR9367 (990), GR8767 (© 1986, 990; per-row digits `[partially verified]`). [cited in: 01b]
- **International Mathematical Olympiad** — *What is IMO?* + *General Regulations (2025)* (6 proof problems, 2×4.5h, 7 pts each). https://www.imo-official.org/about/ ; https://www.imo-official.org/documents/RegulationsIMO.pdf [cited in: 08]
- **Mathematical Association of America (MAA)** — *Putnam* + *Putnam Archive* (12 problems/120; 2026 shift to four 90-min sessions). https://maa.org/putnam/ [cited in: 08]
- **AERA, APA, & NCME (2014).** *Standards for Educational and Psychological Testing.* https://www.aera.net/publications/books/standards-for-educational-psychological-testing-2014-edition [cited in: 11]
- **StatPearls** (Sundjaja, J. H., Shrestha, R., & Krishan, K.). *McNemar And Mann-Whitney U Tests.* NCBI Bookshelf NBK560699. [cited in: 11]

---

## 3. Named experts & books

- Lord, F. M. (1980). *Applications of Item Response Theory to Practical Testing Problems.* [cited in: 03]
- Embretson, S. E., & Reise, S. P. (2000). *Item Response Theory for Psychologists.* [cited in: 03]
- Kolen, M. J., & Brennan, R. L. (2014). *Test Equating, Scaling, and Linking* (3rd ed.). Springer. doi:10.1007/978-1-4939-0317-7 [cited in: 03, 11]
- Gelman, A., et al. *Bayesian Data Analysis.* [cited in: 03]
- Vovk, V., Gammerman, A., & Shafer, G. (2005). *Algorithmic Learning in a Random World* (conformal prediction). [cited in: 03]
- Linacre, J. M. (1994). *Sample Size and Item Calibration Stability.* Rasch Measurement Transactions 7(4):328. https://www.rasch.org/rmt/rmt74m.htm [cited in: 11]
- Schoenfeld, A. H. (1985). *Mathematical Problem Solving.* Academic Press (resources/heuristics/control/beliefs; also Schoenfeld 1979 heuristic-instruction experiment). [cited in: 08, 09]
- Mason, J., Burton, L., & Stacey, K. (1982; 2nd ed. 2010). *Thinking Mathematically.* (specializing/generalizing/conjecturing/convincing). [cited in: 08]
- Anderson, L. W., & Krathwohl, D. R. (eds.) (2001). *A Taxonomy for Learning, Teaching, and Assessing* (revised Bloom). [cited in: 08]
- Webb, N. L. (1997). *Criteria for Alignment of Expectations and Assessments in Mathematics and Science Education* (Depth of Knowledge). CCSSO Research Monograph No. 6. [cited in: 08]
- Polya, G. (1945). *How to Solve It.* Princeton University Press. [cited in: 09]
- Detterman, D. K., & Sternberg, R. J. (eds.) (1993). *Transfer on Trial.* ("Transfer is rare."). [cited in: 09]
- Singley, M. K., & Anderson, J. R. (1989). *The Transfer of Cognitive Skill.* [cited in: 09]
- Robert A. Bjork & Elizabeth L. Bjork — desirable difficulties (Bjork & Bjork 2011; Soderstrom & Bjork 2015, *Perspectives on Psych. Science* 10(2):176–199 — learning-vs-performance, delayed-endpoint rationale); UCLA Bjork Learning & Forgetting Lab. [cited in: 04, 10, 14, 15]
- Spielberger, C. D., Gorsuch, R. L., & Lushene, R. E. (1970; 1983). *Manual for the State-Trait Anxiety Inventory (STAI).* Palo Alto, CA: Consulting Psychologists Press (STAI-state, 20 items, 20–80). [cited in: 14]
- Brooke, J. (1996). *SUS: A "quick and dirty" usability scale.* In P. W. Jordan et al. (eds.), *Usability Evaluation in Industry* (pp. 189–194). Taylor & Francis (10-item System Usability Scale). [cited in: 15]
- Sauro, J., & Lewis, J. R. (2016). *Quantifying the User Experience* (2nd ed.). Morgan Kaufmann (SUS benchmark mean 68, SD 12.5; percentile/grade interpretation). [cited in: 15]
- Hart, S. G., & Staveland, L. E. (1988). *Development of NASA-TLX (Task Load Index): Results of empirical and theoretical research.* In *Human Mental Workload* (pp. 139–183). North-Holland (six subscales; raw/unweighted TLX for cognitive load). [cited in: 15]
- Zeidner, M. (1998). *Test Anxiety: The State of the Art.* New York: Plenum Press. [cited in: 12]
- Ashcraft, M. H. (2002). *Math anxiety: Personal, educational, and cognitive consequences.* Current Directions in Psychological Science 11(5):181–185. [cited in: 12]
- K. Anders Ericsson — deliberate-practice framework (Ericsson 2016 reply, Perspectives on Psych. Science 11(3):351–354). [cited in: 10]
- Dunlosky, J., Rawson, K. A., Marsh, E. J., Nathan, M. J., & Willingham, D. T. (2013). *Improving Students' Learning With Effective Learning Techniques.* (rates spacing/testing "high utility"). [cited in: 04]
- Carvalho, P. F., & Goldstone, R. L. — sequential-attention account of interleaving. [cited in: 04]
- Jarrett (Junyao) Ye / "Expertium" / "L-M-Sherlock" — FSRS algorithm authors & maintainers (DSR model; benchmark). [cited in: 02]
- Piotr Woźniak — SuperMemo theory / forgetting-curve superposition argument. [cited in: 02]
- Terence Tao — *Advice on mathematics competitions* (blog). https://terrytao.wordpress.com/career-advice/advice-on-mathematics-competitions/ [cited in: 08]
- Evan Chen — *Against the 'Research vs. Olympiads' Mantra* (blog). https://blog.evanchen.cc/2016/08/13/against-the-research-vs-olympiads-mantra/ [cited in: 08]
- Kiran Kedlaya — *The Putnam Archive.* https://kskedlaya.org/putnam-archive/ [cited in: 08]
- Damien Elmes (dae) — Anki/AnkiWeb lead developer; maintainer statements on sync conflict resolution (forum thread 26442) and AnkiMobile. [cited in: 05, 06]

---

## 4. Practitioner / blog / vendor (clearly labeled — corroboration only)

- Expertium — FSRS `Benchmark.html` / `Algorithm.html` (FSRS internals; "99.6%/97.4% superiority over SM-2"). `[practitioner; version-dependent]` [cited in: 02]
- Anki Forums — FSRS-vs-SM-2 superiority threads. `[practitioner]` [cited in: 02]
- AnkiWeb FAQ / fsrs4anki tutorial & wiki / awesome-fsrs wiki. `[practitioner]` [cited in: 02]
- Snorkel AI — critic-paradox blog (self-critics can hallucinate flaws). `[vendor]` [cited in: 07]
- OSF / University of Surrey / Australian Treasury — preregistration guidance. `[practitioner/institutional]` [cited in: 07]
- NCSS PASS — *Tests for Two Correlated Proportions (McNemar Test)* documentation, Ch. 150 (power figures). `[vendor doc]` [cited in: 11]
- mathsub.com — form list / rescaling history, and the **unofficial** "2019 Raw Score Conversion Chart" (regression + "educated guesses"). `[unofficial]` [cited in: 01b]
- Rambo Tutoring — "Math GRE" page (enumerates public forms). `[practitioner]` [cited in: 01b]
- mathematicsgre.com — forum threads enumerating available papers. `[practitioner]` [cited in: 01b]
- Kaplan; Magoosh; Marks Education — GRE prep (pacing/format). `[practitioner]`; one Kaplan/practitioner "¼-point penalty" claim judged `[erroneous]` against ETS rights-only scoring. [cited in: 08, 10]
- Study.com — calculator-policy corroboration. `[practitioner]` [cited in: 01]
- Syracuse University (math advising) — topic→course mapping. `[institutional, secondary]` [cited in: 01]
- AwesomeMath (Titu Andreescu-affiliated) — "Why Participate in Math Competitions?" `[marketing; not evidence]` [cited in: 09]
- Wikipedia — *GRE Mathematics Test* (stale mean 659/SD 137 `[SUPERSEDED]`), *IMO*, *Putnam* (format/median-score). `[contested for figures]` [cited in: 01, 01b, 08]

---

## 5. Source code & developer docs (Anki / AnkiDroid ecosystem)

- **ankitects/anki** (Rust `rslib`) — scheduler (`scheduler/answering/`, `scheduler/queue/builder/`), `collection.rs`, `storage/sqlite.rs`, `ops.rs`, `undo/mod.rs`, `proto/anki/*.proto`, `backend/dbproxy.rs`, `storage/upgrades/mod.rs` (`SCHEMA_MAX_VERSION=18`); `rslib/src/sync/` (HttpSyncClient, collection/media syncers). [cited in: 05, 06]
- Anki `docs/architecture.md` — three-tier pylib↔rsbridge↔rslib design. [cited in: 05]
- **DeepWiki** — ankitects/anki source-cited index (commits `8f214453`, `57e67f84`). `[secondary index of source]` [cited in: 05, 06]
- Anki Manual — `syncing.html` (conflict behavior), `sync-server.html` (self-hosted server env vars). [cited in: 05, 06]
- Anki GitHub issues — #2352 (bury/gathering), #2694 (FSRS min-interval clamp), #3094 (FSRS cold-start), #4263 (queue/mtime). [cited in: 05]
- **ankidroid/Anki-Android-Backend** (`rsdroid`) — README + PRs #246, #525 (rsdroid.aar / rsdroid-testing.jar; Rust backend via JNI/protobuf). [cited in: 05, 06]
- AnkiDroid — Database-Structure wiki (USN, revlog `id`=epoch-ms, schema); issue #19508 (undo). [cited in: 05, 06]
- anki-cloud ADR — `rslib/src/sync/` endpoints, WAL/file-locking notes. `[secondary]` [cited in: 06]
- dsnopek/anki-sync-server PR #63 — captured live sync traffic (endpoint names). [cited in: 06]
- ankicommunity `sync_app.py` — server operations list. [cited in: 06]
- AnkiMobile — App Store listing + faqs.ankiweb.net + forum thread 51470 (closed-source; iOS status/pricing). [cited in: 06]
- Criterion.rs — Rust micro-benchmark crate (book + crates.io). [cited in: 06]
- hyperfine — CLI benchmarking tool. [cited in: 06]
- winterfell issue #264 — Criterion public-API limitation. [cited in: 06]
- UniFFI / iOS bridging how-tos (dev.to, boehs.org, strathweb) — `aarch64-apple-ios` static lib + Swift bindings + xcframework. `[practitioner how-to]` [cited in: 06]
- SymPy / SymCode (2025) — computer-algebra verification of generated math. [cited in: 07]
- LMSYS — *LLM Decontaminator* (embedding search + LLM judge). [cited in: 07]
- Google BIG-bench — canary-string convention + `training_on_test_set` task. https://github.com/google/BIG-bench [cited in: 11]
- sklearn `TimeSeriesSplit` — time-ordered CV for calibration. [cited in: 02]

---

## Cross-citation summary (sources used by ≥2 prompts)

- **ETS Practice Book GR3768** — 01, 01b, 08, 10, 11
- **ETS Content & Structure** — 01, 08, 09, 10, 11, 15
- **ETS Subject Test Interpretive Data** (current © 2025 + superseded © 2024) — 01, 01b, 03, 10
- **Kapoor & Narayanan (2023)** — 03, 07, 11
- **Yang et al. (2023), rephrased samples** — 03, 07, 11
- **Pan & Rickard (2018)** — 02, 04, 10, 15
- **Brunmair & Richter (2019)** — 04, 10
- **Bjork & Bjork (2011) / desirable difficulties** — 04, 10, 14, 15
- **Sweller (1988)** — 09, 10
- **Barnett & Ceci (2002)** — 02, 09
- **Rowland (2014)** — 02, 04
- **Adesope et al. (2017)** — 02, 04
- **Kolen & Brennan (2014)** — 03, 11
- **Fagerland et al. (2013)** — 03, 11
- **Brown et al. (2020), GPT-3 contamination** — 03, 07
- **Schoenfeld (1985)** — 08, 09
- **Kaplan / Magoosh practitioner prep** — 08, 10
- **DeepWiki / Anki Manual / ankitects/anki source / AnkiDroid rsdroid** — 05, 06
- **Hembree (1988)** — 12, 13, 14
- **von der Embse et al. (2018)** — 12, 13, 14
- **Huntley et al. (2019)** — 12, 13, 14
- **Jamieson et al. (2010), GRE reappraisal** — 12, 13, 14
- **Jamieson et al. (2016), classroom reappraisal** — 12, 13, 14
- **Ramirez & Beilock (2011)** `[replication-failed]` — 12, 13, 14
- **Camerer et al. (2018), SSRP replications** — 13, 14
- **Beilock & Carr (2005) / Eysenck et al. (2007) ACT** — 12, 13
- **Cassady & Johnson (2002), CTAS** — 12, 14
- **Ergene (2003)** — 12, 14
- **Saunders et al. (1996), SIT** — 09, 13
- **Soderstrom & Bjork (2015)** — 04, 10, 14, 15
- **Meichenbaum & Deffenbacher (1988), SIT** — 13, 14
- **Lakens (2017), TOST** — 04, 14, 15
- **Bridgeman (2012) / Liu et al. (2015), answer review** — 15 _(new Round 4 thread; single-prompt but load-bearing for the interface decision)_
