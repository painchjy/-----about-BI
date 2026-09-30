#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UDOM 元模型 -> OWL/Turtle 导出器
用法: .venv/bin/python tools/owl/export_turtle.py
产出:
  ontology/udom.ttl                          本体（类体系/属性/基数限制/枚举/规则注解）
  ontology/examples/fulfillment.example.ttl  示例实例
  poc/after-sales.candidate.ttl              PoC 实例
映射规则:
  类型 -> owl:Class（五层为中间类，继承 Element 基座）
  关系 -> owl:ObjectProperty（domain/range，多类型取 owl:unionOf）
  card 1 / 1..* / 0..1 -> owl 基数限制（R1/R2/R7）；ctx_pattern -> 子属性
  枚举 -> 个体；规则 R1-R10 -> udom:ConstraintRule 注解
命名空间 https://ontodomain.dev/udom# 为占位符，正式部署前替换为组织 IRI。
"""
import datetime
import os
import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
NS = 'https://ontodomain.dev/udom#'
ONTO_IRI = 'https://ontodomain.dev/udom'
TODAY = datetime.date.today().isoformat()

HEADER = '''@prefix udom: <https://ontodomain.dev/udom#> .
@prefix owl:  <http://www.w3.org/2002/07/owl#> .
@prefix rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .
@prefix dcterms: <http://purl.org/dc/terms/> .
'''

LAYER_CLASS = {'kernel': 'KernelElement', 'motivation': 'MotivationElement',
               'domain': 'DomainElement', 'agent': 'AgentElement', 'asset': 'AssetElement'}
PROP_RENAME = {'side_effects': 'sideEffects', 'retrieval_strategy': 'retrievalStrategy',
               'context_budget_tokens': 'contextBudgetTokens', 'doc_title': 'docTitle',
               'doc_type': 'docType', 'pass_criteria': 'passCriteria', 'kind': 'subKind'}
ENUM_PROPS = {'status', 'origin', 'docType', 'enforcement', 'autonomy', 'subKind',
              'sideEffects', 'technique', 'severity', 'likelihood', 'criticality',
              'tier', 'action', 'pattern'}
DICT_FLATTEN = {'metric': ['name', 'unit', 'target', 'baseline', 'deadline'],
                'charter': ['scope_in', 'scope_out']}


def esc(s):
    return str(s).replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ')


def lit(v):
    if isinstance(v, bool):
        return '"' + str(v).lower() + '"^^xsd:boolean'
    if isinstance(v, int):
        return '"' + str(v) + '"^^xsd:integer'
    if isinstance(v, float):
        return '"' + str(v) + '"^^xsd:decimal'
    return '"' + esc(v) + '"'


def union(classes):
    if len(classes) == 1:
        return 'udom:' + classes[0]
    return '[ a owl:Class ; owl:unionOf ( ' + ' '.join('udom:' + c for c in classes) + ' ) ]'


def zh_label(kind, desc):
    zh = (desc or '').split('——')[0].split('，')[0].strip()
    return zh or kind


def eind(attr, value):
    return 'udom:enum_' + attr + '_' + str(value)


def load_meta():
    with open(os.path.join(ROOT, 'ontology', 'metamodel.yaml'), encoding='utf-8') as f:
        return yaml.safe_load(f)


def emit_ontology(meta):
    out = [HEADER]
    out.append('<{iri}> a owl:Ontology ;\n'
               '    owl:versionInfo "{ver}" ;\n'
               '    rdfs:label "UDOM 统一领域本体"@zh ;\n'
               '    rdfs:label "Unified Domain Ontology Metamodel"@en ;\n'
               '    rdfs:comment "整合 BMM(业务动机)×DDD(领域驱动设计)×AgentOps(智能体工程) 的领域建模本体；由 metamodel.yaml 自动生成，请勿手工编辑"@zh ;\n'
               '    dcterms:source "ontology/metamodel.yaml" ;\n'
               '    dcterms:created "{today}"^^xsd:date .'
               .format(iri=ONTO_IRI, ver=meta['version'], today=TODAY))

    out.append('# ===== 基座与五层 =====\n'
               'udom:Element a owl:Class ; rdfs:label "元素（抽象基座）"@zh ;\n'
               '    rdfs:comment "所有模型元素的基座：id/name/status/ns/provenance/evidence"@zh .\n\n'
               'udom:hasStatus a owl:ObjectProperty ; rdfs:label "治理状态"@zh ; rdfs:domain udom:Element ; rdfs:range udom:Status .\n'
               'udom:hasOrigin a owl:ObjectProperty ; rdfs:label "来源"@zh ; rdfs:domain udom:Element ; rdfs:range udom:Origin .\n'
               'udom:evidencedBy a owl:ObjectProperty ; rdfs:label "证据溯源"@zh ; rdfs:domain udom:Element ; rdfs:range udom:Evidence ;\n'
               '    rdfs:comment "每个元素应有 >=1 条证据（R6, warn）"@zh .\n'
               'udom:ns a owl:DatatypeProperty ; rdfs:label "命名空间/域分区"@zh .\n'
               'udom:agentName a owl:DatatypeProperty ; rdfs:label "产出智能体"@zh .\n'
               'udom:confidence a owl:DatatypeProperty ; rdfs:label "置信度"@zh .\n'
               'udom:alias a owl:DatatypeProperty ; rdfs:label "别名"@zh .\n'
               'udom:clues a owl:DatatypeProperty ; rdfs:label "抽取线索"@zh .')
    layers = meta.get('layers', {})
    for key, cls in LAYER_CLASS.items():
        info = layers.get(key, {})
        out.append('udom:{c} a owl:Class ; rdfs:subClassOf udom:Element ;\n'
                   '    rdfs:label "{n}"@zh ; rdfs:comment "{p}"@zh .'
                   .format(c=cls, n=esc(info.get('name', key)), p=esc(info.get('purpose', ''))))

    out.append('# ===== 类型（按层） =====')
    for kind, spec in meta['types'].items():
        parent = 'udom:Element' if kind == 'Evidence' else 'udom:' + LAYER_CLASS[spec['layer']]
        block = 'udom:{k} a owl:Class ;\n    rdfs:subClassOf {p} ;\n' \
                '    rdfs:label "{zh}"@zh ; rdfs:label "{k}"@en ;\n' \
                '    rdfs:comment "{d}"@zh'.format(k=kind, p=parent,
                    zh=esc(zh_label(kind, spec.get('desc', ''))), d=esc(spec.get('desc', '')))
        if spec.get('clues'):
            block += ' ;\n    udom:clues "' + esc(','.join(map(str, spec['clues']))) + '"'
        out.append(block + ' .')

    out.append('# ===== 元素属性 =====')
    seen = {}
    for kind, spec in meta['types'].items():
        for aname, aspec in (spec.get('attrs') or {}).items():
            prop = PROP_RENAME.get(aname, aname)
            if prop in seen or aname in DICT_FLATTEN:
                continue
            seen[prop] = True
            ptype = 'owl:ObjectProperty' if prop in ENUM_PROPS else 'owl:DatatypeProperty'
            out.append('udom:{p} a {t} ; rdfs:label "{l}"@zh .'
                       .format(p=prop, t=ptype, l=esc(aspec.get('desc', aname))))
    for base, keys in DICT_FLATTEN.items():
        for k in keys:
            camel = base + k[:1].upper() + k[1:]
            out.append('udom:{c} a owl:DatatypeProperty ; rdfs:label "{b}.{k}"@zh .'
                       .format(c=camel, b=base, k=k))

    out.append('# ===== 关系（对象属性） =====')
    for rel, spec in meta['relations'].items():
        out.append('udom:{r} a owl:ObjectProperty ;\n    rdfs:domain {d} ;\n    rdfs:range {g} ;\n'
                   '    rdfs:comment "card={c}"@zh .'
                   .format(r=rel, d=union(spec['from']), g=union(spec['to']),
                           c=spec.get('card', '0..*')))
    out.append('# contextRelationship 的模式子属性（R9 词汇表）')
    for ptn in meta.get('enums', {}).get('ctx_pattern', []):
        out.append('udom:ctx_{p} a owl:ObjectProperty ; rdfs:subPropertyOf udom:contextRelationship ;\n'
                   '    rdfs:label "上下文关系:{p}"@zh .'.format(p=ptn))
    return '\n\n'.join(out) + '\n'


def emit_restrictions(meta):
    out = ['# ===== 基数限制（对应 R1/R2/R7 等） =====']
    suffix = '"^^xsd:nonNegativeInteger'
    for rel, spec in meta['relations'].items():
        card = spec.get('card', '0..*')
        if card == '0..*':
            continue
        rng = union(spec['to'])
        pred = {'1': 'owl:qualifiedCardinality "1',
                '1..*': 'owl:minQualifiedCardinality "1',
                '0..1': 'owl:maxQualifiedCardinality "1'}.get(card)
        note = {'1': '恰好 1', '1..*': '至少 1', '0..1': '至多 1'}.get(card)
        if not pred:
            continue
        for src in spec['from']:
            out.append('udom:{s} rdfs:subClassOf [ a owl:Restriction ; owl:onProperty udom:{r} ;\n'
                       '    owl:onClass {g} ; {p}{suf} ] .  # {n}'
                       .format(s=src, r=rel, g=rng, p=pred, suf=suffix, n=note))
    out.append('udom:Skill rdfs:subClassOf [ a owl:Restriction ; owl:onProperty udom:realizes ;\n'
               '    owl:onClass udom:BusinessCapability ; owl:minQualifiedCardinality "1' + suffix + ' ] .  # R7')
    return '\n\n'.join(out) + '\n'


def emit_enums(meta):
    out = ['# ===== 枚举类与个体 =====',
           'udom:Status a owl:Class ; rdfs:label "治理状态"@zh .',
           'udom:Origin a owl:Class ; rdfs:label "来源"@zh .']
    cls_map = {'status': 'udom:Status', 'origin': 'udom:Origin'}
    for ename, values in meta.get('enums', {}).items():
        for v in values:
            out.append('{i} a {c} ; rdfs:label "{v}"@en .'
                       .format(i=eind(ename, v), c=cls_map.get(ename, 'owl:NamedIndividual'), v=v))
    for kind, spec in meta['types'].items():
        for aname, aspec in (spec.get('attrs') or {}).items():
            vals = aspec.get('enum')
            if isinstance(vals, list):
                prop = PROP_RENAME.get(aname, aname)
                for v in vals:
                    out.append('{i} a owl:NamedIndividual ; rdfs:label "{v}"@en .'
                               .format(i=eind(prop, v), v=v))
    return '\n'.join(out) + '\n'


def emit_rules(meta):
    out = ['# ===== 约束规则注解（SHACL 形状属 v0.2，此处文档化） =====',
           'udom:ConstraintRule a owl:Class ; rdfs:label "约束规则"@zh .',
           'udom:severity a owl:DatatypeProperty ; rdfs:label "严重级别"@zh .']
    for r in meta.get('rules', []):
        out.append('udom:{i} a udom:ConstraintRule ; rdfs:label "{i}"@en ;\n'
                   '    udom:severity "{lv}" ; rdfs:comment "{d}"@zh .'
                   .format(i=r['id'], lv=r['level'], d=esc(r['desc'])))
    return '\n\n'.join(out) + '\n'


def emit_instance(meta, inst, prefix, base):
    out = [HEADER.replace('@prefix dcterms:',
                          '@prefix ' + prefix + ': <' + base + '> .\n@prefix dcterms:')]
    m = inst.get('model', {})
    out.append('<{b}> a owl:Ontology ; owl:imports <{iri}> ;\n'
               '    rdfs:label "{n}（实例）"@zh ; owl:versionInfo "udom={v}" .'
               .format(b=base.rstrip('#'), iri=ONTO_IRI, n=esc(m.get('name', prefix)),
                       v=m.get('udom', '?')))

    for e in inst.get('elements', []) or []:
        eid, kind = e['id'], e['kind']
        lines = ['{p}:{i} a udom:{k} ;'.format(p=prefix, i=eid, k=kind),
                 '    rdfs:label "{n}"@zh ;'.format(n=esc(e.get('name', eid)))]
        if e.get('description'):
            lines.append('    rdfs:comment "{d}"@zh ;'.format(d=esc(e['description'])))
        if e.get('ns'):
            lines.append('    udom:ns "{v}" ;'.format(v=esc(e['ns'])))
        if e.get('status'):
            lines.append('    udom:hasStatus {i} ;'.format(i=eind('status', e['status'])))
        prov = e.get('provenance') or {}
        if prov.get('origin'):
            lines.append('    udom:hasOrigin {i} ;'.format(i=eind('origin', prov['origin'])))
        if prov.get('agent'):
            lines.append('    udom:agentName "{v}" ;'.format(v=esc(prov['agent'])))
        if prov.get('confidence') is not None:
            lines.append('    udom:confidence {v} ;'.format(v=lit(prov['confidence'])))
        for ev in e.get('evidence', []) or []:
            lines.append('    udom:evidencedBy {p}:{ev} ;'.format(p=prefix, ev=ev))
        for aname, val in (e.get('attrs') or {}).items():
            if aname in DICT_FLATTEN and isinstance(val, dict):
                for k, v in val.items():
                    camel = aname + k[:1].upper() + k[1:]
                    for item in (v if isinstance(v, list) else [v]):
                        lines.append('    udom:{c} {x} ;'.format(c=camel, x=lit(item)))
                continue
            prop = PROP_RENAME.get(aname, aname)
            if prop in ENUM_PROPS:
                lines.append('    udom:{p} {i} ;'.format(p=prop, i=eind(prop, val)))
            else:
                for item in (val if isinstance(val, list) else [val]):
                    lines.append('    udom:{p} {x} ;'.format(p=prop, x=lit(item)))
        lines[-1] = lines[-1].rstrip(' ;') + ' .'
        out.append('\n'.join(lines))

    for r in inst.get('relations', []) or []:
        rt = r['type']
        if rt == 'contextRelationship' and (r.get('attrs') or {}).get('pattern'):
            rt = 'ctx_' + r['attrs']['pattern']
        out.append('{p}:{s} udom:{r} {p}:{t} .'.format(p=prefix, s=r['source'], r=rt, t=r['target']))

    qs = inst.get('questions') or []
    if qs:
        out.append('udom:Question a owl:Class ; rdfs:label "待确认问题"@zh .')
        for q in qs:
            out.append('[ a udom:Question ; rdfs:label "{a}"@zh ;\n'
                       '   rdfs:comment "{t}"@zh ] .'
                       .format(a=esc(q.get('about', '')), t=esc(q.get('text', ''))))
    return '\n\n'.join(out) + '\n'


def main():
    meta = load_meta()
    ttl = '\n'.join([emit_ontology(meta), emit_restrictions(meta), emit_enums(meta), emit_rules(meta)])
    jobs = [('ontology/udom.ttl', ttl),
            ('ontology/examples/fulfillment.example.ttl',
             emit_instance(meta, yaml.safe_load(open(os.path.join(ROOT, 'ontology/examples/fulfillment.example.yaml'), encoding='utf-8')),
                           'ful', 'https://ontodomain.dev/example/fulfillment#')),
            ('poc/after-sales.candidate.ttl',
             emit_instance(meta, yaml.safe_load(open(os.path.join(ROOT, 'poc/after-sales.candidate.yaml'), encoding='utf-8')),
                           'as', 'https://ontodomain.dev/example/after-sales#'))]
    for path, content in jobs:
        full = os.path.join(ROOT, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, 'w', encoding='utf-8') as f:
            f.write(content)
        print('生成', path, '(', len(content) // 1024, 'KB )')


if __name__ == '__main__':
    main()
