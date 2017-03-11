#!/usr/bin/env python
# -*- coding: utf-8 -*-

def test_true():
    assert True

def test_spanish_translator_instantiation():
    from nlp_component.translators import SpanishTranslator as Translator
    es = Translator()
    assert es.translate("Muestra neuronas Mi1 en medula") =="Show Mi1 neurons in medulla"

def test_french_translator_instantiation():
    from nlp_component.translators import FrenchTranslator as Translator
    fr = Translator()
    assert fr.translate("Montres les neurones Mi1 dans la medulla") =="Show Mi1 neurons in medulla"

def test_romanian_translator_instantiation():
    from nlp_component.translators import RomanianTranslator as Translator
    ro = Translator()
    assert ro.translate("Afiseaza neuronii glutamatergici locali din antennal lobe") =="Show local glutamatergic neurons in antennal lobe"
