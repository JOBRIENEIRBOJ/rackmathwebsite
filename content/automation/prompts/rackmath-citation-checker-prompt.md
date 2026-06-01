# RackMath Citation Checker Prompt

Use this prompt before publishing any RackMath article that includes health, science, or training claims.

```txt
Check the citations in this RackMath article.

For each factual health, science, or training claim:

1. Tell me whether the claim needs a citation.
2. Tell me whether the current citation supports the claim.
3. Flag any unsupported or overstated claim.
4. Suggest a safer rewrite if needed.
5. Remove or rewrite claims that are not supported.
6. Return a final clean version in Markdown with frontmatter.

Citation rules:
- Do not invent citations.
- Do not cite a source unless it directly supports the claim.
- Do not overstate research.
- Prefer simple, safe claims.
- Use reputable sources such as CDC, WHO, ACSM, NIH, Mayo Clinic, Cleveland Clinic, and PubMed.
```

## Claims That Usually Need Citations

Cite claims about:

- How often adults should strength train
- Physical activity guidelines
- Muscle strengthening recommendations
- Aging and muscle loss
- Bone health
- Injury risk
- Health benefits
- Disease risk
- Research findings
- Medical outcomes
- Specific statistics

## Claims That Usually Do Not Need Citations

Usually no citation needed for:

- "Start with a lighter weight."
- "Track your sets."
- "Ask gym staff for help."
- "Use a weight you can control."
- "Do not make the plan too complicated."
- "It is normal to feel awkward when you are new."

## Safe Claim Rewrites

Risky:

> Lifting weights prevents injury.

Safer:

> Learning good form and using weights you can control can make lifting more manageable for beginners.

Risky:

> Strength training prevents disease.

Safer:

> Strength training is part of the physical activity plan recommended by major health organizations.

Risky:

> Everyone should lift heavy weights.

Safer:

> Many beginners benefit from starting with manageable resistance and building gradually.

Risky:

> Strength training is the best exercise for aging.

Safer:

> Strength training can help adults maintain strength and function as they age.

## Preferred Citation Sources

### CDC

Use for adult physical activity guidelines.

https://www.cdc.gov/physical-activity-basics/guidelines/adults.html

### WHO

Use for global physical activity recommendations.

https://www.who.int/initiatives/behealthy/physical-activity

### ACSM

Use for exercise and resistance training guidance.

https://acsm.org/education-resources/trending-topics-resources/physical-activity-guidelines/

https://acsm.org/resistance-training-guidelines-update-2026/

### NIH / National Institute on Aging

Use for exercise, aging, strength, function, and older adults.

https://www.nia.nih.gov/health/exercise-and-physical-activity

### Mayo Clinic

Use for general strength training benefits.

https://www.mayoclinic.org/healthy-lifestyle/fitness/in-depth/strength-training/art-20046670

### Cleveland Clinic

Use for plain-language strength training education.

https://health.clevelandclinic.org/strength-training

## Final Citation Check

Before publishing, confirm:

- Every source is real.
- Every source is relevant.
- Every cited claim is supported.
- No source is used to support a claim it does not actually make.
- Medical claims are not overstated.
- The article still sounds simple and human.
