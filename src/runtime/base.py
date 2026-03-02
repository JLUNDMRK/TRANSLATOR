class BaseRuntime:
    def translate(self, text: str) -> str:
        raise NotImplementedError

    def infer_failure_mode(
        self,
        original_text: str,
        translated_text: str,
        dtc_codes,
        component_codes,
        sw_versions,
        dtc_entries,
    ) -> dict:
        raise NotImplementedError
