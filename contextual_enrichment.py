import re
import json
from datetime import datetime, timezone

from parser import extrair_contrato, extrair_processo
from normalizer import normalize_contrato, normalize_processo

RE_INSTITUTIONAL_CONTRATANTE = re.compile(r'(?i)(?<!PELO\s)(?<!PELA\s)CONTRATANTE\s*:', re.IGNORECASE)
RE_PELO_CONTRATANTE = re.compile(r'(?i)PELO\s+CONTRATANTE\b', re.IGNORECASE)


def _has_institutional_contratante_in_text(text):
    if not text:
        return False
    # True only if 'Contratante:' present and not 'PELO CONTRATANTE'
    if RE_INSTITUTIONAL_CONTRATANTE.search(text) and not RE_PELO_CONTRATANTE.search(text):
        return True
    return False


def aplicar_regra_001_heranca_contratante(prev_block_text, prev_metadados, prev_numero,
                                         curr_block_text, curr_metadados, curr_numero, pdf_path):
    """
    Regra 001: Herança do contratante institucional do bloco anterior para o bloco atual.

    Condições (todas obrigatórias):
      - existe bloco anterior
      - blocos são consecutivos (prev_numero == curr_numero - 1)
      - mesmo PDF (pdf_path passado para ambos)
      - bloco anterior possui contratante institucional (rótulo 'Contratante:' e não 'PELO CONTRATANTE')
      - bloco atual não possui contratante institucional
      - mesmo contrato OU mesmo processo (determinístico)

    Ação: copia prev_metadados['contratante'] para curr_metadados['contratante'] (se presente),
    sem alterar nenhum texto_bloco.

    Retorna: (curr_metadados_updated, applied_flag, audit_record_dict)
    """

    applied = False
    audit = None

    # Condição 1: existe bloco anterior
    if prev_block_text is None or prev_metadados is None:
        return curr_metadados, False, None

    # Condição 2: consecutivos
    try:
        if not (prev_numero == curr_numero - 1):
            return curr_metadados, False, None
    except Exception:
        return curr_metadados, False, None

    # Condição 3: mesmo PDF - caller ensures pdf context; we accept pdf_path param as context
    # no-op here (we assume caller ensures same pdf)

    # Condição 4: prev possui contratante institucional (label 'Contratante:' presente and not 'PELO CONTRATANTE')
    prev_has_institutional = _has_institutional_contratante_in_text(prev_block_text)
    if not prev_has_institutional:
        return curr_metadados, False, None

    # Condição 5: curr não possui contratante institucional
    curr_has_institutional = _has_institutional_contratante_in_text(curr_block_text)
    if curr_has_institutional:
        return curr_metadados, False, None

    # Condição 6: mesmo contrato OU mesmo processo (determinístico)
    contrato_prev = prev_metadados.get('contrato')
    contrato_curr = curr_metadados.get('contrato')

    processo_prev = prev_metadados.get('processo')
    processo_curr = curr_metadados.get('processo')

    same_contract = False
    same_process = False

    if contrato_prev and contrato_curr:
        # normalize simple textual representation
        def _norm(s):
            return re.sub(r"\s+", "", (s or '').upper())
        try:
            same_contract = _norm(contrato_prev) == _norm(contrato_curr)
        except Exception:
            same_contract = False

    if processo_prev and processo_curr and not same_contract:
        def _normp(s):
            return re.sub(r"\s+", "", (s or '').upper())
        try:
            same_process = _normp(processo_prev) == _normp(processo_curr)
        except Exception:
            same_process = False

    # Determine availability of contrato/processo values
    prev_contratante = prev_metadados.get('contratante')
    curr_contratante = curr_metadados.get('contratante')

    if not prev_contratante:
        return curr_metadados, False, None

    # Determine criterion used (A, B or C)
    criterion = None
    if same_contract:
        criterion = 'A'
    elif same_process:
        criterion = 'B'
    else:
        # Implement criterion C: check if normalized contrato_prev appears in curr_block_text
        def _text_contains_normalized_contract(text, norm_contract):
            if not text or not norm_contract:
                return False
            # normalize text by removing spaces around punctuation to match normalize_contrato behavior
            text_norm = re.sub(r"\s*([./-])\s*", r"\1", text)
            # simple case-insensitive search
            return norm_contract.lower() in text_norm.lower()

        norm_prev = normalize_contrato(contrato_prev) if contrato_prev else None
        norm_curr = normalize_contrato(contrato_curr) if contrato_curr else None

        if norm_prev and _text_contains_normalized_contract(curr_block_text, norm_prev):
            criterion = 'C'
        elif norm_curr and _text_contains_normalized_contract(prev_block_text, norm_curr):
            criterion = 'C'

    if not criterion:
        return curr_metadados, False, None

    # Apply substitution: overwrite contratante even if curr had value
    previous_value = curr_contratante
    updated = dict(curr_metadados)
    updated['contratante'] = prev_contratante

    applied = True

    audit = {
        'rule': 'REGRA_001_HERANCA_CONTRATANTE',
        'pdf_path': pdf_path,
        'prev_numero_bloco': prev_numero,
        'curr_numero_bloco': curr_numero,
        'contrato_prev': contrato_prev,
        'contrato_curr': contrato_curr,
        'processo_prev': processo_prev,
        'processo_curr': processo_curr,
        'previous_contratante': previous_value,
        'inherited_contratante': prev_contratante,
        'criterion': criterion,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }

    # Emitir log estruturado para auditoria (linha por evento) usando logging
    try:
        import logging
        logger = logging.getLogger('diario_processor.enrichment')
        logger.info(json.dumps({'enrichment_audit': audit}, ensure_ascii=False))
    except Exception:
        # fail silently on logging
        pass

    return updated, applied, audit
