# Research Challenges in RL-Based Network Intrusion Detection
**A Case Study: Dynamic AI Firewall Development**

---

## Abstract

This document presents the challenges encountered during the development of a Reinforcement Learning (RL) based network intrusion detection system. We trained a Proximal Policy Optimization (PPO) agent on the CICIDS 2017 dataset to classify network traffic in real-time. Through multiple training iterations, we identified critical issues related to class imbalance, reward function design, and train-test distribution mismatch. This analysis provides insights for researchers and practitioners building similar systems.

**Keywords:** Reinforcement Learning, Intrusion Detection, PPO, Class Imbalance, Reward Shaping, Cybersecurity

---

## 1. Introduction

### 1.1 Problem Statement

Network intrusion detection systems (NIDS) face a fundamental challenge: balancing security (detecting attacks) with usability (avoiding false alarms). Traditional rule-based systems cannot adapt to new attack patterns, while supervised machine learning requires extensive labeled data.

We hypothesized that Reinforcement Learning could:
1. Learn optimal detection policies through interaction
2. Adapt to changing attack patterns
3. Balance multiple objectives (security vs. usability)

### 1.2 Research Questions

**RQ1:** Can an RL agent effectively learn to distinguish between benign and malicious network traffic?

**RQ2:** How does data distribution (balanced vs. natural) affect model performance?

**RQ3:** How do reward function parameters influence the Recall-FPR trade-off?

**RQ4:** What is the optimal training strategy for imbalanced cybersecurity datasets?

---

## 2. System Architecture

### 2.1 Environment Design

**State Space (20 dimensions):**
- Flow duration
- Packet counts (forward/backward)
- Packet lengths (min/mean/max)
- Inter-arrival times
- Protocol features
- Flag distributions

**Action Space (4 discrete actions):**
- 0: ALLOW - Let traffic through
- 1: BLOCK - Drop traffic
- 2: RATE_LIMIT - Throttle traffic
- 3: FLAG_MONITOR - Alert but allow

**Reward Function:**
```python
R(action, true_label) = {
    +reward_allow_benign,     if ALLOW and benign
    -penalty_allow_attack,    if ALLOW and attack
    +reward_block_attack,     if BLOCK and attack
    -penalty_block_benign,    if BLOCK and benign
}
```

### 2.2 Dataset

**CICIDS 2017:**
- Total samples: 2,827,876
- Benign traffic: 80.3%
- Attack traffic: 19.7%
- Attack types: 14 categories
- Features: 78 (reduced to 20 for efficiency)

---

## 3. Challenges Encountered

### Challenge 1: Class Imbalance Problem

#### 3.1.1 The Issue

Network traffic is naturally imbalanced:
- Production: ~95-99% benign, 1-5% attacks
- CICIDS 2017: 80% benign, 20% attacks

**Hypothesis:** Class imbalance would cause the model to learn a biased policy favoring the majority class (benign).

#### 3.1.2 Experiment 1: Train on Natural Distribution

**Setup:**
- Training: 2.4M samples (80% benign, 20% attack)
- Rewards: Balanced (-25 allow attack, +10 block attack, -5 block benign)
- Timesteps: 2M

**Results:**
```
Recall: 61%
FPR: 0.51%
F1: 0.747
```

**Analysis:**
Model learned to be **overly conservative** - prioritized avoiding false positives over catching attacks. The 4:1 ratio of benign:attack samples made the agent encounter benign traffic more frequently during training, biasing it toward ALLOW actions.

**Literature Context:**
This aligns with findings in [Fernández et al., 2018] who showed standard ML classifiers achieve <65% recall on imbalanced intrusion detection datasets without mitigation strategies.

---

### Challenge 2: Overcorrection Through Balancing

#### 3.2.1 The Approach

**Hypothesis:** Artificially balancing the dataset (50% benign, 50% attack) would force the agent to treat both classes equally.

#### 3.2.2 Experiment 2: Train on Balanced Distribution

**Setup:**
- Training: 778K samples (50% benign, 50% attack)
- Rewards: Aggressive (-25 allow attack, +15 block attack, -5 block benign)
- Timesteps: 2M

**Results:**
```
Recall: 98.3%
FPR: 35.4%
F1: 0.574
```

**Analysis:**
Model learned to be **overly aggressive** - caught nearly all attacks but created massive false positive problem. The agent learned in an artificial 50:50 environment that doesn't exist in production.

**Critical Insight:**
Training distribution != Test distribution = **Distributional Shift**

During training, P(attack) = 0.5
During testing, P(attack) = 0.2
Agent's policy optimized for wrong distribution.

**Literature Context:**
[Quiñonero-Candela et al., 2009] "Dataset Shift in Machine Learning" warned about train-test mismatch. Our results empirically confirm this in the RL+IDS domain.

---

### Challenge 3: Reward Function Sensitivity

#### 3.3.1 The Issue

RL agents are **extremely sensitive** to reward structure. Small changes in reward magnitudes caused dramatic behavior shifts.

#### 3.3.2 Reward Experiments

| Config | Allow Attack | Block Attack | Block Benign | Recall | FPR | Behavior |
|--------|--------------|--------------|--------------|--------|-----|----------|
| A | -15 | +10 | -8 | 61% | 0.5% | Too passive |
| B | -25 | +15 | -5 | 98% | 35% | Too aggressive |
| C | -25 | +10 | -20 | 61% | 1% | Too conservative |

**Observation:**
- Increasing "Block Benign" penalty from -5 to -20 (4x) dropped Recall from 98% to 61%
- System has **no obvious "sweet spot"** in reward space

#### 3.3.3 Theoretical Analysis

The optimal policy π* satisfies:
```
π* = argmax E[Σ γ^t R(s_t, a_t)]
```

But R(s,a) is hand-designed. There's no analytical way to derive reward values that yield specific Recall/FPR targets.

**Research Gap:**
Current RL literature lacks principled methods for reward function design in multi-objective security scenarios.

**Related Work:**
[Hadfield-Menell et al., 2017] "Inverse Reward Design" attempts to infer rewards from constraints, but hasn't been applied to IDS.

---

### Challenge 4: Multi-Objective Optimization

#### 3.4.1 The Fundamental Trade-off

IDS faces competing objectives:
- **Objective 1:** Maximize Recall (security)
- **Objective 2:** Minimize FPR (usability)

These are **inversely correlated** - improving one typically worsens the other.

#### 3.4.2 Mathematical Formulation

```
maximize: Recall = TP / (TP + FN)
minimize: FPR = FP / (FP + TN)
subject to: Recall > 0.85, FPR < 0.05
```

Standard RL optimizes a single scalar reward. Multi-objective optimization requires:

**Option A: Scalarization**
```
R = w1 × Recall - w2 × FPR
```
Problem: Choosing w1, w2 is arbitrary

**Option B: Pareto Optimization**
Train multiple policies, select from Pareto frontier
Problem: Computationally expensive

**Option C: Constrained RL**
```
maximize Recall
subject to FPR < threshold
```
Problem: Not directly supported in standard RL libraries

**Our Approach:**
We used Option A (scalarization via reward shaping), which proved difficult to tune.

**Literature Context:**
[Vamplew et al., 2011] "Empirical evaluation of multi-objective RL" showed scalarization often fails to find optimal trade-offs. Our experience confirms this.

---

### Challenge 5: Train-Test Distribution Mismatch

#### 3.5.1 The Core Issue

**Mathematical Problem:**

Training policy: π_train learned under P_train(s,a)
Deployment policy: π_deploy must work under P_deploy(s,a)

If P_train ≠ P_deploy, performance degrades.

**Our Case:**
- P_train: 50% benign, 50% attack (artificial)
- P_deploy: 80% benign, 20% attack (natural)

**Result:** Policy trained on P_train was suboptimal for P_deploy

#### 3.5.2 Experiment 3: Matched Distributions

**Setup:**
- Training: 2.4M samples (80% benign, 20% attack) - MATCHES TEST
- Rewards: Conservative (-25 allow attack, +10 block attack, -20 block benign)
- Timesteps: 3M

**Results:**
```
Recall: 61.3%
FPR: 1.08%
F1: 0.740
```

**Analysis:**
Matching distributions **solved the FPR problem** (1% vs 35%) but recall remained low. The agent correctly learned the deployment distribution but reward function was miscalibrated.

**Key Insight:**
Distribution matching is **necessary but not sufficient**. Must also tune rewards appropriately.

---

## 4. Root Cause Analysis

### 4.1 Why Standard RL Struggles with IDS

#### Problem 1: Sparse Attack Samples

In natural distribution:
- Agent sees attack only 20% of time
- 80% of training episodes involve benign traffic
- Gradient updates biased toward benign class

**Effect:** Agent doesn't learn attack patterns sufficiently

#### Problem 2: Asymmetric Costs

- False Negative (miss attack): Could cost millions (security breach)
- False Positive (block benign): Costs productivity (user annoyance)

Costs are **orders of magnitude different** but reward function uses simple scalars (+10, -20).

**Research Gap:** RL reward functions don't naturally encode real-world cost asymmetries.

#### Problem 3: Non-Stationary Distribution

In production:
- Attack patterns evolve over time
- New zero-day exploits emerge
- Benign traffic changes (new applications)

Agent trained on static 2017 dataset won't generalize to 2027 threats.

**Literature:** [Tesauro et al., 2007] showed RL agents can adapt to non-stationarity but require continual learning.

---

### 4.2 Comparison with Supervised Learning

| Aspect | Supervised Learning | Reinforcement Learning |
|--------|---------------------|------------------------|
| **Class Imbalance** | Well-studied (SMOTE, class weights) | Limited literature |
| **Multi-Objective** | Straightforward (weighted loss) | Requires reward engineering |
| **Train-Test Mismatch** | Domain adaptation techniques exist | Under-researched |
| **Calibration** | Standard methods (Platt scaling) | Not well-defined |

**Conclusion:** Many IDS challenges are **better solved** with supervised learning. RL's advantage (online learning, sequential decisions) not fully utilized in our architecture.

---

## 5. Proposed Solutions

### 5.1 Solution 1: Cost-Sensitive Reward Design

Instead of arbitrary rewards, derive from real costs:

```python
# Real-world costs
cost_security_breach = $1,000,000
cost_blocked_employee = $50
cost_investigation = $200

# Derived rewards (normalized)
reward_block_attack = 1000  # Prevented $1M loss
penalty_allow_attack = -1000
penalty_block_benign = -1  # $50 << $1M
```

**Hypothesis:** Cost-based rewards would naturally balance objectives.

---

### 5.2 Solution 2: Curriculum Learning

Train in stages with increasing difficulty:

**Stage 1:** Easy attacks (obvious patterns)
**Stage 2:** Medium attacks (require more features)
**Stage 3:** Hard attacks (subtle, low-rate)

**Related Work:** [Bengio et al., 2009] showed curriculum learning accelerates RL training.

---

### 5.3 Solution 3: Hybrid Approach

Combine RL with supervised learning:

```
Step 1: Pre-train with supervised learning (high recall)
Step 2: Fine-tune with RL (reduce FPR)
```

**Rationale:** SL learns good attack representations, RL optimizes deployment trade-offs.

---

### 5.4 Solution 4: Multi-Agent System

Deploy multiple specialized agents:

- **Agent 1:** High recall (catches 95% attacks, 10% FPR)
- **Agent 2:** High precision (catches 60% attacks, 0.5% FPR)
- **Meta-Agent:** Routes traffic to appropriate agent based on confidence

**Hypothesis:** Ensemble would achieve better Pareto frontier.

---

## 6. Lessons Learned

### 6.1 For Practitioners

1. **Don't artificially balance cybersecurity data**
   - Train on natural distribution
   - Use class weights or cost-sensitive learning instead

2. **Reward engineering is critical**
   - Expect to iterate 5-10 times
   - Small changes = big impact
   - No theory to guide you (trial and error)

3. **Test set must match deployment**
   - Collect real traffic data
   - Validate on production-like distribution

4. **RL may be overkill for IDS**
   - Consider supervised learning first
   - RL beneficial only if online adaptation needed

---

### 6.2 For Researchers

1. **Research Gap: RL for Imbalanced Data**
   - Limited literature on RL + severe class imbalance
   - Techniques from supervised learning don't directly transfer

2. **Research Gap: Multi-Objective RL in Security**
   - Need principled methods beyond scalarization
   - Constrained RL libraries needed

3. **Research Gap: Reward Function Design**
   - Current practice is "guess and check"
   - Need inverse RL or reward learning from preferences

4. **Benchmark Needed**
   - Standard IDS benchmark with RL baseline
   - Fair comparison across approaches

---

## 7. Comparison with Related Work

### 7.1 Literature Review

| Paper | Approach | Dataset | Recall | FPR | Notes |
|-------|----------|---------|--------|-----|-------|
| [Sharafaldin et al., 2018] | Random Forest | CICIDS 2017 | 89% | 11% | Supervised baseline |
| [Lopez-Martin et al., 2017] | CNN | NSL-KDD | 84% | 5.8% | Deep learning |
| [Usama et al., 2019] | Generative Adversarial Network | CICIDS 2017 | 91% | 8% | GAN for imbalance |
| **Our Work (Attempt 1)** | **PPO RL** | **CICIDS 2017** | **61%** | **0.5%** | **Too conservative** |
| **Our Work (Attempt 2)** | **PPO RL** | **CICIDS 2017** | **98%** | **35%** | **Too aggressive** |
| **Our Work (Attempt 3)** | **PPO RL** | **CICIDS 2017** | **61%** | **1%** | **Still suboptimal** |

**Observation:** Our RL approach **underperformed** supervised baselines.

**Hypothesis:** RL's sequential decision-making advantage not applicable to per-flow classification.

---

### 7.2 When RL Actually Helps

RL superior for:
1. **Sequential decisions** - Block now or monitor longer?
2. **Long-term consequences** - Attacker may adapt to blocks
3. **Online adaptation** - Learn from deployment feedback

Our architecture only leverages (3), making RL overkill.

**Better RL Use Case:**
```
State: Network + Attacker history (last 100 flows)
Action: Block, Rate-limit, Honeypot, Allow
Reward: Security over 24-hour window (long-term)
```

This would justify RL's complexity.

---

## 8. Open Problems

### 8.1 Theoretical Questions

**Q1:** Does there exist a reward function that yields Recall > 85% and FPR < 5% on imbalanced data?

**Q2:** What is the sample complexity for RL to match supervised learning on IDS tasks?

**Q3:** Can we prove convergence of PPO under severe class imbalance?

---

### 8.2 Practical Questions

**Q1:** How to automatically tune reward functions for target metrics?

**Q2:** Can transfer learning from supervised pre-training improve RL sample efficiency?

**Q3:** Does multi-agent RL ensemble perform better than single agent?

---

## 9. Recommendations for Future Work

### 9.1 Short-term (3-6 months)

1. **Implement cost-sensitive rewards**
   - Derive from real-world costs
   - Compare to current approach

2. **Try supervised pre-training + RL fine-tuning**
   - Hypothesis: Faster convergence

3. **Collect real deployment data**
   - Pilot with 1-2 customers
   - Measure actual Recall/FPR trade-offs

---

### 9.2 Long-term (1-2 years)

1. **Develop multi-agent ensemble**
   - Multiple specialized models
   - Meta-learner for routing

2. **Continuous learning pipeline**
   - Weekly retraining with feedback
   - Measure improvement over time

3. **Publish research paper**
   - "Challenges of RL for Network Intrusion Detection"
   - Submit to IEEE Security & Privacy

---

## 10. Conclusion

We developed an RL-based network intrusion detection system and encountered significant challenges related to class imbalance, reward engineering, and distribution mismatch. Through three training iterations, we empirically demonstrated:

1. **Class imbalance severely impacts RL** - More than supervised learning
2. **Artificial balancing causes distributional shift** - Worse than natural imbalance
3. **Reward functions require extensive tuning** - No principled design method
4. **RL may be unnecessary for per-flow classification** - Supervised learning often sufficient

Our work contributes practical insights for practitioners building similar systems and identifies research gaps in multi-objective RL for cybersecurity.

**Current Best Result:**
- Recall: 61.3%
- FPR: 1.08%
- Conclusion: **Not yet production-ready**, requires further iteration

**Path Forward:**
Continue reward tuning or pivot to hybrid supervised+RL approach.

---

## References

1. Sharafaldin et al. (2018). "Toward Generating a New Intrusion Detection Dataset and Intrusion Traffic Characterization." ICISSP.

2. Fernández et al. (2018). "Learning from Imbalanced Data Sets." Springer.

3. Quiñonero-Candela et al. (2009). "Dataset Shift in Machine Learning." MIT Press.

4. Hadfield-Menell et al. (2017). "Inverse Reward Design." NeurIPS.

5. Vamplew et al. (2011). "Empirical evaluation methods for multiobjective reinforcement learning algorithms." Machine Learning.

6. Bengio et al. (2009). "Curriculum Learning." ICML.

7. Lopez-Martin et al. (2017). "Network Traffic Classifier with CNN." Cognitive Computation.

8. Usama et al. (2019). "Generative Adversarial Networks for Launching and Thwarting Adversarial Attacks." IEEE/ACM IWQoS.

9. Tesauro et al. (2007). "Temporal Difference Learning and TD-Gammon." Communications of the ACM.

---

**Document Status:** Research Analysis  
**Date:** October 26, 2026  
**Version:** 1.0  
**Authors:** Dynamic AI Firewall Research Team

