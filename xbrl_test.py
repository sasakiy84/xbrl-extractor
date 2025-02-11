from itertools import islice
from pathlib import Path

from xbrl_utils import (
    BSInstance,
    PLInstance,
    CFInstance,
    get_bs_concepts,
    get_cf_concepts,
    get_pl_concepts,
    load_edinet_xbrl_model_from_zip,
)

XBRL_ARCHIVE_FILES = Path("xbrl-files").glob("**/*_xbrl.zip")
XBRL_ARCHIVE_FILES = list(
    islice(XBRL_ARCHIVE_FILES, 155 + 61 + 223 + 208 + 353, 100000)
)


total_file_count = len(XBRL_ARCHIVE_FILES)
for i, xbrl_folder in enumerate(XBRL_ARCHIVE_FILES):
    print(f"[{i + 1}/{total_file_count}] {xbrl_folder}")
    xbrl_model, ctrlr = load_edinet_xbrl_model_from_zip(xbrl_folder)

    bs_concepts = get_bs_concepts(xbrl_model)

    bs_instances: list[BSInstance] = []
    for bs in bs_concepts:
        instances = bs.extract_instances()
        bs_instances.extend(instances)

        # print(bs.to_str_recursively)
        # for instance in instances:
        #     print(instance.model_dump_json(indent=2))

    pl_concepts = get_pl_concepts(xbrl_model)
    pl_instances: list[PLInstance] = []
    for pl in pl_concepts:
        instances = pl.extract_instances()
        pl_instances.extend(instances)

        # print(pl.to_str_recursively)
        # for instance in instances:
        #     print(instance.model_dump_json(indent=2))

    cf_concepts = get_cf_concepts(xbrl_model)
    cf_instances: list[CFInstance] = []
    for cf in cf_concepts:
        instances = cf.extract_instances()
        cf_instances.extend(instances)

        # print(cf.to_str_recursively)
        # for instance in instances:
        #     print(instance.model_dump_json(indent=2))

    ctrlr.close()
