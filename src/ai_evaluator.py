') and content.endswith('```'):
                lines = content.split('\n')
                # Remove first line (```json or just ```)
                lines = lines[1:]
                # Remove last line (