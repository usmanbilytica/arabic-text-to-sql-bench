# Gulf Text-to-SQL Bench

[![Hugging Face dataset](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Dataset-FFD21E)](https://huggingface.co/datasets/usmanbilytica/gulf-text-to-sql-bench) [![Release](https://img.shields.io/github/v/release/usmanbilytica/arabic-text-to-sql-bench)](https://github.com/usmanbilytica/arabic-text-to-sql-bench/releases) [![License: MIT](https://img.shields.io/badge/code-MIT-blue)](LICENSE) [![Data: CC BY 4.0](https://img.shields.io/badge/data-CC%20BY%204.0-lightgrey)](https://creativecommons.org/licenses/by/4.0/)

**Can your LLM answer a business question asked in Gulf Arabic?**

Most Text-to-SQL benchmarks are English-only. In Saudi Arabia and the wider GCC, real users ask the same question three ways: in English, in Modern Standard Arabic, and in everyday Gulf dialect. This benchmark tests all three on the same database, so you can see exactly where a model's accuracy drops.

| | Question | Expected answer |
|---|---|---|
| English | How many employees belong to the Al-Qahtani family? | 51 |
| Modern Standard Arabic | كم عدد الموظفين من عائلة القحطاني؟ | 51 |
| Gulf dialect | كم واحد من القحاطين عندنا؟ | 51 |

The dialect version uses the tribal plural *القحاطين*. The data only contains *القحطاني*. A model has to know they mean the same family.

## What it tests

The database models two Saudi public-sector systems: **HR** (employees, departments, grades, salaries in SAR) and **municipal permits** (building, commercial, signage and excavation permits, plus inspections), across 5 regions and 11 cities. Reference data is bilingual and personal names are in Arabic.

The 30 questions (×3 language variants = 90 test items) target the problems we keep seeing in production:

- **Answer language:** an Arabic question should get Arabic names back (`name_ar`), an English one English names
- **Gulf dialect:** *وش*, *الحين*, *للحين*, *طاحت* (failed), *شغّال* (active), *عطني*
- **Arabic-Indic digits:** *٢٠٢٥* instead of 2025
- **Region vs city:** *منطقة الرياض* (the region) is not the city of Riyadh
- **Domain terms:** *نسبة السعودة* (Saudization rate), *على رأس العمل* (active), *المرتبة* (civil service grade)
- Standard SQL skills: joins, group-by, ratios, date arithmetic, anti-joins, correlated subqueries

Levels: 9 easy, 15 medium, 6 hard.

## Quick start

No dependencies beyond Python 3.8+.

```bash
python build_db.py                 # builds gulf_gov.db (deterministic, seed 2026)
python evaluate.py --gold-check    # sanity check: should print 100% for every variant
python make_prompts.py > prompts.jsonl
```

Send each prompt to your model, then save the answers as JSON Lines:

```json
{"id": "hr-008", "variant": "ar_gulf", "sql": "SELECT COUNT(*) FROM employees WHERE full_name_ar LIKE '%القحطاني'"}
```

and score them:

```bash
python evaluate.py predictions.jsonl
```

```
variant     correct  total  accuracy
en               ..     30      ..%
ar_msa           ..     30      ..%
ar_gulf          ..     30      ..%
```

## Scoring

Execution accuracy. The predicted query is run on the database and its result is compared with the gold result:

- row order is ignored (multiset comparison)
- extra columns are fine, as long as the gold columns appear among them in the same order
- numbers are rounded to 2 decimals; percentages are on a 0–100 scale

## Files

| File | What it is |
|---|---|
| `questions.jsonl` | Questions in `en`, `ar_msa`, `ar_gulf`, with gold SQL (`sql_en` when the English answer differs) |
| `build_db.py` | Schema and deterministic synthetic data generator |
| `evaluate.py` | Execution-accuracy scorer |
| `make_prompts.py` | Model-agnostic prompts with the full schema |

## Results

No results yet. Run your model and open a pull request that adds a row here, including the model name, date and prompt setup.

| Model | en | ar_msa | ar_gulf | Submitted by |
|---|---|---|---|---|
| | | | | |

## Roadmap

- More questions, written and reviewed by native speakers from different Gulf countries
- More domains: healthcare appointments, retail, government finance
- Hijri dates and fiscal-year questions
- Schema-linking difficulty: Arabic column names and abbreviations

## Contributing

New questions are very welcome. Each one needs all three variants, gold SQL that passes `python evaluate.py --gold-check`, and a non-empty answer. If you speak a different Gulf dialect (Emirati, Kuwaiti, Omani, Qatari, Bahraini), dialect variants are especially valuable. Please open an issue to discuss bigger changes first.

<div dir="rtl">

## بالعربية

**هل يفهم نموذجك سؤالاً عن البيانات بلهجة خليجية؟**

معظم مقاييس تحويل الأسئلة إلى استعلامات SQL باللغة الإنجليزية فقط. هذا المقياس يطرح السؤال نفسه بثلاث صيغ: الإنجليزية، والعربية الفصحى، واللهجة الخليجية، على قاعدة بيانات واحدة تحاكي أنظمة الموارد البشرية والتراخيص البلدية في المملكة العربية السعودية.

- ٣٠ سؤالاً بثلاث صيغ، أي ٩٠ حالة اختبار
- تقييم بدقة التنفيذ على قاعدة بيانات SQLite
- نرحّب بمساهمات المتحدثين بلهجات الخليج المختلفة

</div>

## License

Code: MIT. Questions and data: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The data is synthetic; any resemblance to real people is coincidental.

## Citation

```bibtex
@misc{ahmad2026gulftext2sql,
  author       = {Usman Ahmad},
  title        = {Gulf Text-to-SQL Bench: English, Modern Standard Arabic and Gulf Dialect},
  year         = {2026},
  howpublished = {\url{https://github.com/usmanbilytica/arabic-text-to-sql-bench}}
}
```

---

Created by [Usman Ahmad](https://www.linkedin.com/in/usmanahmad), Co-Founder & Global CEO of [Bilytica](https://bilytica.sa).
