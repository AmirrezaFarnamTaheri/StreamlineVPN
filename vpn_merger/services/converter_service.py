from typing import Dict, List
import base64
import json


class MultiFormatConverter:
    """Lightweight converter placeholder. Extend with real formatters later."""

    def convert_to_all_formats(self, configs: List[str]) -> Dict[str, str]:
        raw_text = "\n".join(configs)
        outputs: Dict[str, str] = {
            'raw': raw_text,
            'base64': base64.b64encode(raw_text.encode('utf-8')).decode('utf-8'),
        }
        try:
            outputs['json'] = json.dumps({'configs': configs}, ensure_ascii=False)
        except Exception:
            outputs['json'] = ''
        return outputs


