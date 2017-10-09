from base import api
from base.constants import (
    ONE_TO_SIX_ON_WINDOWS,
    ONE_TO_SIX_WITH_SPACES,
    ONE_TO_SIX_WITH_TABS,
)
from base.populators import (
    DatasetPopulator,
    skip_without_datatype,
)

from galaxy.tools.verify.test_data import TestDataResolver


class ToolsUploadTestCase(api.ApiTestCase):

    def setUp(self):
        super(ToolsUploadTestCase, self).setUp()
        self.dataset_populator = DatasetPopulator(self.galaxy_interactor)

    def test_upload1_paste(self):
        with self.dataset_populator.test_history() as history_id:
            payload = self.dataset_populator.upload_payload(history_id, 'Hello World')
            create_response = self._post("tools", data=payload)
            self._assert_has_keys(create_response.json(), 'outputs')

    def test_upload_posix_newline_fixes(self):
        windows_content = ONE_TO_SIX_ON_WINDOWS
        result_content = self._upload_and_get_content(windows_content)
        self.assertEquals(result_content, ONE_TO_SIX_WITH_TABS)

    def test_upload_disable_posix_fix(self):
        windows_content = ONE_TO_SIX_ON_WINDOWS
        result_content = self._upload_and_get_content(windows_content, to_posix_lines=None)
        self.assertEquals(result_content, windows_content)

    def test_upload_tab_to_space(self):
        table = ONE_TO_SIX_WITH_SPACES
        result_content = self._upload_and_get_content(table, space_to_tab="Yes")
        self.assertEquals(result_content, ONE_TO_SIX_WITH_TABS)

    def test_upload_tab_to_space_off_by_default(self):
        table = ONE_TO_SIX_WITH_SPACES
        result_content = self._upload_and_get_content(table)
        self.assertEquals(result_content, table)

    @skip_without_datatype("rdata")
    def test_rdata_not_decompressed(self):
        # Prevent regression of https://github.com/galaxyproject/galaxy/issues/753
        rdata_path = TestDataResolver().get_filename("1.RData")
        rdata_metadata = self._upload_and_get_details(open(rdata_path, "rb"), file_type="auto")
        self.assertEquals(rdata_metadata["file_ext"], "rdata")

    @skip_without_datatype("velvet")
    def test_composite_datatype(self):
        with self.dataset_populator.test_history() as history_id:
            dataset = self._velvet_upload(history_id, extra_inputs={
                "files_1|url_paste": "roadmaps content",
                "files_1|type": "upload_dataset",
                "files_2|url_paste": "log content",
                "files_2|type": "upload_dataset",
            })

            roadmaps_content = self._get_roadmaps_content(history_id, dataset)
            assert roadmaps_content.strip() == "roadmaps content", roadmaps_content

    @skip_without_datatype("velvet")
    def test_composite_datatype_space_to_tab(self):
        # Like previous test but set one upload with space_to_tab to True to
        # verify that works.
        with self.dataset_populator.test_history() as history_id:
            dataset = self._velvet_upload(history_id, extra_inputs={
                "files_1|url_paste": "roadmaps content",
                "files_1|type": "upload_dataset",
                "files_1|space_to_tab": "Yes",
                "files_2|url_paste": "log content",
                "files_2|type": "upload_dataset",
            })

            roadmaps_content = self._get_roadmaps_content(history_id, dataset)
            assert roadmaps_content.strip() == "roadmaps\tcontent", roadmaps_content

    @skip_without_datatype("velvet")
    def test_composite_datatype_posix_lines(self):
        # Like previous test but set one upload with space_to_tab to True to
        # verify that works.
        with self.dataset_populator.test_history() as history_id:
            dataset = self._velvet_upload(history_id, extra_inputs={
                "files_1|url_paste": "roadmaps\rcontent",
                "files_1|type": "upload_dataset",
                "files_1|space_to_tab": "Yes",
                "files_2|url_paste": "log\rcontent",
                "files_2|type": "upload_dataset",
            })

            roadmaps_content = self._get_roadmaps_content(history_id, dataset)
            assert roadmaps_content.strip() == "roadmaps\ncontent", roadmaps_content

    def test_upload_dbkey(self):
        with self.dataset_populator.test_history() as history_id:
            payload = self.dataset_populator.upload_payload(history_id, "Test123", dbkey="hg19")
            run_response = self.dataset_populator.tools_post(payload)
            self.dataset_populator.wait_for_tool_run(history_id, run_response)
            datasets = run_response.json()["outputs"]
            assert datasets[0].get("genome_build") == "hg19", datasets[0]

    def test_upload_multiple_files_1(self):
        with self.dataset_populator.test_history() as history_id:
            payload = self.dataset_populator.upload_payload(history_id, "Test123",
                dbkey="hg19",
                extra_inputs={
                    "files_1|url_paste": "SecondOutputContent",
                    "files_1|NAME": "SecondOutputName",
                    "files_1|file_type": "tabular",
                    "files_1|dbkey": "hg18",
                    "file_count": "2",
                }
            )
            run_response = self.dataset_populator.tools_post(payload)
            self.dataset_populator.wait_for_tool_run(history_id, run_response)
            datasets = run_response.json()["outputs"]

            assert len(datasets) == 2, datasets
            content = self.dataset_populator.get_history_dataset_content(history_id, dataset=datasets[0])
            assert content.strip() == "Test123"
            assert datasets[0]["file_ext"] == "txt"
            assert datasets[0]["genome_build"] == "hg19", datasets

            content = self.dataset_populator.get_history_dataset_content(history_id, dataset=datasets[1])
            assert content.strip() == "SecondOutputContent"
            assert datasets[1]["file_ext"] == "tabular"
            assert datasets[1]["genome_build"] == "hg18", datasets

    def test_upload_multiple_files_2(self):
        with self.dataset_populator.test_history() as history_id:
            payload = self.dataset_populator.upload_payload(history_id, "Test123",
                file_type="tabular",
                dbkey="hg19",
                extra_inputs={
                    "files_1|url_paste": "SecondOutputContent",
                    "files_1|NAME": "SecondOutputName",
                    "files_1|file_type": "txt",
                    "files_1|dbkey": "hg18",
                    "file_count": "2",
                }
            )
            run_response = self.dataset_populator.tools_post(payload)
            self.dataset_populator.wait_for_tool_run(history_id, run_response)
            datasets = run_response.json()["outputs"]

            assert len(datasets) == 2, datasets
            content = self.dataset_populator.get_history_dataset_content(history_id, dataset=datasets[0])
            assert content.strip() == "Test123"
            assert datasets[0]["file_ext"] == "tabular", datasets
            assert datasets[0]["genome_build"] == "hg19", datasets

            content = self.dataset_populator.get_history_dataset_content(history_id, dataset=datasets[1])
            assert content.strip() == "SecondOutputContent"
            assert datasets[1]["file_ext"] == "txt"
            assert datasets[1]["genome_build"] == "hg18", datasets

    def test_upload_multiple_files_3(self):
        with self.dataset_populator.test_history() as history_id:
            payload = self.dataset_populator.upload_payload(history_id, "Test123",
                file_type="tabular",
                dbkey="hg19",
                extra_inputs={
                    "files_0|file_type": "txt",
                    "files_0|dbkey": "hg18",
                    "files_1|url_paste": "SecondOutputContent",
                    "files_1|NAME": "SecondOutputName",
                    "files_1|file_type": "txt",
                    "files_1|dbkey": "hg18",
                    "file_count": "2",
                }
            )
            run_response = self.dataset_populator.tools_post(payload)
            self.dataset_populator.wait_for_tool_run(history_id, run_response)
            datasets = run_response.json()["outputs"]

            assert len(datasets) == 2, datasets
            content = self.dataset_populator.get_history_dataset_content(history_id, dataset=datasets[0])
            assert content.strip() == "Test123"
            assert datasets[0]["file_ext"] == "txt", datasets
            assert datasets[0]["genome_build"] == "hg18", datasets

            content = self.dataset_populator.get_history_dataset_content(history_id, dataset=datasets[1])
            assert content.strip() == "SecondOutputContent"
            assert datasets[1]["file_ext"] == "txt"
            assert datasets[1]["genome_build"] == "hg18", datasets

    def test_upload_multiple_files_space_to_tab(self):
        with self.dataset_populator.test_history() as history_id:
            payload = self.dataset_populator.upload_payload(history_id,
                content=ONE_TO_SIX_WITH_SPACES,
                file_type="tabular",
                dbkey="hg19",
                extra_inputs={
                    "files_0|file_type": "txt",
                    "files_0|space_to_tab": "Yes",
                    "files_1|url_paste": ONE_TO_SIX_WITH_SPACES,
                    "files_1|NAME": "SecondOutputName",
                    "files_1|file_type": "txt",
                    "files_2|url_paste": ONE_TO_SIX_WITH_SPACES,
                    "files_2|NAME": "ThirdOutputName",
                    "files_2|file_type": "txt",
                    "files_2|space_to_tab": "Yes",
                    "file_count": "3",
                }
            )
            run_response = self.dataset_populator.tools_post(payload)
            self.dataset_populator.wait_for_tool_run(history_id, run_response)
            datasets = run_response.json()["outputs"]

            assert len(datasets) == 3, datasets
            content = self.dataset_populator.get_history_dataset_content(history_id, dataset=datasets[0])
            assert content == ONE_TO_SIX_WITH_TABS

            content = self.dataset_populator.get_history_dataset_content(history_id, dataset=datasets[1])
            assert content == ONE_TO_SIX_WITH_SPACES

            content = self.dataset_populator.get_history_dataset_content(history_id, dataset=datasets[2])
            assert content == ONE_TO_SIX_WITH_TABS

    def test_multiple_files_posix_lines(self):
        with self.dataset_populator.test_history() as history_id:
            payload = self.dataset_populator.upload_payload(history_id,
                content=ONE_TO_SIX_ON_WINDOWS,
                file_type="tabular",
                dbkey="hg19",
                extra_inputs={
                    "files_0|file_type": "txt",
                    "files_0|to_posix_lines": "Yes",
                    "files_1|url_paste": ONE_TO_SIX_ON_WINDOWS,
                    "files_1|NAME": "SecondOutputName",
                    "files_1|file_type": "txt",
                    "files_1|to_posix_lines": None,
                    "files_2|url_paste": ONE_TO_SIX_ON_WINDOWS,
                    "files_2|NAME": "ThirdOutputName",
                    "files_2|file_type": "txt",
                    "file_count": "3",
                }
            )
            run_response = self.dataset_populator.tools_post(payload)
            self.dataset_populator.wait_for_tool_run(history_id, run_response)
            datasets = run_response.json()["outputs"]

            assert len(datasets) == 3, datasets
            content = self.dataset_populator.get_history_dataset_content(history_id, dataset=datasets[0])
            assert content == ONE_TO_SIX_WITH_TABS

            content = self.dataset_populator.get_history_dataset_content(history_id, dataset=datasets[1])
            assert content == ONE_TO_SIX_ON_WINDOWS

            content = self.dataset_populator.get_history_dataset_content(history_id, dataset=datasets[2])
            assert content == ONE_TO_SIX_WITH_TABS

    def _velvet_upload(self, history_id, extra_inputs):
        payload = self.dataset_populator.upload_payload(
            history_id,
            "sequences content",
            file_type="velvet",
            extra_inputs=extra_inputs,
        )
        run_response = self.dataset_populator.tools_post(payload)
        self.dataset_populator.wait_for_tool_run(history_id, run_response)
        datasets = run_response.json()["outputs"]

        assert len(datasets) == 1
        dataset = datasets[0]

        return dataset

    def _get_roadmaps_content(self, history_id, dataset):
        roadmaps_content = self.dataset_populator.get_history_dataset_content(history_id, dataset=dataset, filename="Roadmaps")
        return roadmaps_content

    def _upload_and_get_content(self, content, **upload_kwds):
        history_id, new_dataset = self._upload(content, **upload_kwds)
        return self.dataset_populator.get_history_dataset_content(history_id, dataset=new_dataset)

    def _upload_and_get_details(self, content, **upload_kwds):
        history_id, new_dataset = self._upload(content, **upload_kwds)
        return self.dataset_populator.get_history_dataset_details(history_id, dataset=new_dataset)

    def _upload(self, content, **upload_kwds):
        history_id = self.dataset_populator.new_history()
        new_dataset = self.dataset_populator.new_dataset(history_id, content=content, **upload_kwds)
        self.dataset_populator.wait_for_history(history_id, assert_ok=True)
        return history_id, new_dataset