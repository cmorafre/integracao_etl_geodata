select   
  ped.codi_emp, emp.desc_mun, 
  PED.PEDI_PED, PED.SERI_PED, PED.DEMI_PED,
  TRA.CODI_TRA, TRA.CGC_TRA, TRA.RAZA_TRA,
  PRO.PROP_PRO, PRO.DESC_PRO, CIC.CODI_CIC,
  CIC.DESC_CIC, CON.COND_CON, CON.DESC_CON,
  PES.CODI_PES, PES.NOME_PES, TOP.CODI_TOP,
  TOP.DESC_TOP, CFO.CCFO_CFO, CFO.DESC_CFO,
  PED.VCTO_PED, PED.VENC_PFP, VLR.CODI_IND, VLR.DESC_IND, 
  VLR.VLOR_VLR, PED.TOTA_PED, PED.TOTA_PED / COALESCE(VLR.VLOR_VLR,1) TOTA_OM_PED,
  PSV.CODI_PSV, PSV.DESC_PSV, 
  PSV.CODI_GPR, PSV.DESC_GPR, PSV.CODI_SBG, PSV.DESC_SBG,
  PSV.CODI_TRA COD_FABRICANTE, PSV.RAZA_TRA FABRICANTE,
  ped.qtde_ipe QTDE_PEDIDA,
  case
     when TIPO_PED = 'VN' THEN ped.ENTR_PED
     ELSE coalesce(nta.qent_ino,0)
  END QTDE_ENTREGUE,
  ped.QPER_IPE QTDE_PERDIDA, 
   case
     when TIPO_PED = 'VN' THEN  ped.qtde_ipe -  ped.QPER_IPE - ped.ENTR_PED 
     ELSE ped.qtde_ipe - ped.QPER_IPE - coalesce(nta.qdev_ino,0) - coalesce(nta.qent_ino,0) 
  END SALDO,
  ped.qtde_ipe / COALESCE(VLR.VLOR_VLR,1)  QTDE_PEDIDA_OM,
  case
     when TIPO_PED = 'VN' THEN ped.ENTR_PED / COALESCE(VLR.VLOR_VLR,1)
     ELSE coalesce(nta.qent_ino,0) / COALESCE(VLR.VLOR_VLR,1)
  END QTDE_ENTREGUE_OM,
  ped.QPER_IPE / COALESCE(VLR.VLOR_VLR,1) QTDE_PERDIDA_OM, 
   case
     when TIPO_PED = 'VN' THEN  (ped.qtde_ipe -  ped.QPER_IPE - ped.ENTR_PED) / COALESCE(VLR.VLOR_VLR,1) 
     ELSE (ped.qtde_ipe - ped.QPER_IPE - coalesce(nta.qdev_ino,0) - coalesce(nta.qent_ino,0)) / COALESCE(VLR.VLOR_VLR,1) 
  END SALDO_OM,
  PED.VLIQ_IPE VLR_UNIT , (PED.VLIQ_IPE / COALESCE(VLR.VLOR_VLR,1)) VLR_UNIT_OM,
  ped.qtde_ipe * PED.VLIQ_IPE TOTAL_ITEM,
  (ped.qtde_ipe * PED.VLIQ_IPE) / COALESCE(VLR.VLOR_VLR,1) TOTAL_ITEM_OM,
  PED.CTAB_IPE CUST_TAB , PED.CTAB_IPE/ COALESCE(VLR.VLOR_VLR,1) CUST_TAB_OM,
  CTA.TABE_CTA, CTA.DESC_CTA,
  USU.NOME_PES USU_INCLUSAO,
  --(select cust_med FROM BENTIVI.TABLE(custo_medio(PED.CODI_EMP, PED.CODI_PSV, CURRENT_dATE))) CUSTO_MEDIO,.
  CCPD_IPE CUSTO_COMPRA, PRINCIPIO_ATIVO, UNID_PSV UNIDADE, 
  CASE
     WHEN  NEG.MOED_IND = 'R' THEN 'REAL'
     WHEN NEG.MOED_IND = 'D' THEN 'DOLAR'
     ELSE NULL
  END MOEDA_RT , 
  NEG.VLUL_NEG RT,
  vneg.vlor_vlr COTACAO_DOLAR,
  (SELECT VLIQ_INF FROM 
  (
   SELECT NFE.CODI_EMP, INF.CODI_PSV, INF.VLIQ_INF , NFE.DREC_NFE FROM BENTIVI.NFENTRA NFE
       INNER JOIN BENTIVI.INFENTRA INF ON INF.CTRL_NFE = NFE.CTRL_NFE AND
                                  INF.CODI_TRA = NFE.CODI_TRA AND
                                  INF.SERI_NFE = NFE.SERI_NFE AND
                                  INF.NUME_NFE = NFE.NUME_NFE AND
                                  INF.CODI_EMP = NFE.CODI_EMP 
       INNER JOIN BENTIVI.CFO ON CFO.CCFO_CFO = NFE.CCFO_CFO
       INNER JOIN BENTIVI.FUNCAOTOPER F  ON (F.CODI_TOP = NFE.CODI_TOP)   
       WHERE        
         F.CODI_PTO = 1 AND
         INF.CODI_PSV = PSV.CODI_PSV AND       
         CFO.COMP_CFO <> '2'       
       ORDER BY NFE.DREC_NFE DESC, NFE.NUME_NFE DESC
  ) WHERE ROWNUM <= 1) ULT_COMPRA, pedo_ped PEDIDO_ORIGEM,
  neg.nume_neg NUMERO_NEGOCIACAO, 
   NEG.TIPO_NEG TIPO_NEGOCIACAO, 
   NEG.RT_LIQUIDA ,
   NEG.COTACAO_DL_NEG COTACAO_DOLAR_NEGOCIACAO,
   NUME_CCP CONTRATO_BARTER,
   VENDA_PERDIDA_REAL     
from 
   (
      select 
      ipe.codi_psv, ipe.codi_emp, ped.codi_top, ped.codi_cic,ped.demi_ped,
      ipe.qtde_ipe, PED.PEDI_PED, PED.SERI_PED, PED.CODI_tRA, PED.PROP_PRO, 
      PED.COND_CON, PED.COD1_PES CODI_PES, PED.CCFO_CFO, PED.VCTO_PED,
      coalesce(ipe.QPER_IPE,0) QPER_IPE, PED.DATA_VLR, PED.CODI_IND,
      (select qent FROM TABLE(BENTIVI.QTDE_ENTR_PED_VEN(ped.codi_emp, ped.pedi_ped, ped.seri_ped, ipe.codi_psv))) ENTR_PED,
      CASE 
         WHEN NOT EXISTS (SELECT * FROM BENTIVI.TOPCTRL T WHERE T.CODI_TOP = PED.CODI_TOP AND T.CODI_CTR = 5) THEN 'VN'
         ELSE 'VF'
      END TIPO_PED,
      PED.TOTA_PED, IPE.VLIQ_IPE, IPE.CTAB_IPE, IPE.TABE_CTA, PED.CODI_USU,
      (SELECT LISTAGG( to_date(VENC_PFP,'dd/mm/yyyy'),';') WITHIN GROUP (ORDER BY VENC_PFP) VENC_PFP FROM(
        select 
           ped.VCTO_PED + PRAZ_PFP VENC_PFP, PFP.CODI_EMP, PFP.PEDI_PED, PFP.SERI_PED
        FROM BENTIVI.PREFINAN PFP) F WHERE F.CODI_EMP = ped.CODI_EMP AND
                                 F.PEDI_PED = ped.PEDI_PED AND
                                 F.SERI_PED = ped.SERI_PED) VENC_PFP, CCPD_IPE, CTRL_NEG, COD1_PES, pedo_ped, PED.NUME_CCP,
      coalesce((select sum(pv.qtde_oco) FROM BENTIVI.OCORRENCIAS pv where pv.pedi_ped = ped.pedi_ped and
                                                    pv.seri_ped = ped.seri_ped and
                                                    pv.codi_emp = ped.codi_emp and
                                                    pv.codi_psv = ipe.codi_psv and
                                                    pv.codi_prv <> 12 AND pv.codi_prv <> 7),0) VENDA_PERDIDA_REAL
      FROM BENTIVI.PEDIDO ped
      inner JOIN BENTIVI.IPEDIDO ipe on ipe.codi_emp = ped.codi_emp and
                          ipe.pedi_ped = ped.pedi_ped and
                          ipe.seri_ped = ped.seri_ped       
      where  ped.SITU_PED <> '9'       
   ) ped 
LEFT JOIN 
  (
  select 
   neg.nume_neg, neg.ctrl_neg, neg.codi_pes, neg.CODI_EMP, 
   case
      when neg.TIPO_NEG = 1 then 'REAL' 
      when neg.TIPO_NEG = 2 then 'DOLAR'
      when (neg.TIPO_NEG = 3) AND (MOED_IND='R') then 'TROCA-REAL'
      when (neg.TIPO_NEG = 3) AND (MOED_IND='D') then 'TROCA-DOLAR'
   END TIPO_NEG , 
   VLUC_NEG RT_LIQUIDA ,
   CASE
      when (neg.TIPO_NEG = 3) AND (MOED_IND='D') THEN VLR.VLOR_VLR
      ELSE NULL
   END COTACAO_DL_NEG
  FROM BENTIVI.NEGOCIACAO neg
  LEFT JOIN BENTIVI.INDVALOR VLR ON VLR.CODI_IND = NEG.CODI_IND AND
                            VLR.CODI_EMP = NEG.CODI_EMP AND
                            VLR.DATA_VLR = NEG.DATA_VLR
  ) NEG ON NEG.CTRL_NEG = PED.CTRL_NEG AND
           NEG.CODI_PES = PED.COD1_PES AND
           NEG.CODI_EMP = PED.CODI_EMP
left join 
 (select 
     sum(ino.qtde_ino) qtde_ino, 
     sum(coalesce(ino.qdev_ino,0)) qdev_ino, 
     sum(coalesce(ino.qent_ino,0)) qent_ino,
     ino.pedi_ped, ino.seri_ped, ino.codi_psv,
     ino.EMPR_PED
  FROM BENTIVI.INOTA ino 
  inner JOIN BENTIVI.NOTA nta on nta.npre_not = ino.npre_not
  where 
     nta.situ_not <> '9' and 
     ino.pedi_ped is not null AND
     ino.seri_ped is not null AND
     ino.EMPR_PED is not null 
  group by 
     ino.pedi_ped, ino.seri_ped, ino.codi_psv,
     ino.EMPR_PED) nta on nta.pedi_ped = PED.pedi_ped and
                          nta.seri_ped = PED.seri_ped and
                          nta.EMPR_PED = PED.codi_emp and
                          nta.codi_psv = PED.codi_psv
inner join 
   (select 
       emp.codi_emp, mun.desc_mun 
    FROM BENTIVI.CADEMP emp 
    inner JOIN BENTIVI.MUNICIPIO mun on mun.codi_mun = emp.codi_mun) emp on emp.codi_emp = ped.codi_emp
inner join 
    (select tra.codi_tra, tra.raza_tra, tra.cgc_tra FROM BENTIVI.TRANSAC tra) tra on tra.codi_tra = ped.codi_tra 
LEFT JOIN 
    (SELECT PROP_PRO, DESC_PRO FROM BENTIVI.PROPRIED) PRO ON PRO.PROP_PRO = PED.PROP_PRO 
LEFT JOIN 
    (SELECT CODI_CIC, DESC_CIC FROM BENTIVI.CICLO) CIC ON CIC.CODI_CIC = PED.CODI_CIC
LEFT JOIN 
    (SELECT 
        CON.COND_CON, CON.DESC_CON
     FROM BENTIVI.CONDICAO CON
     ) CON ON CON.COND_CON = PED.COND_CON
LEFT JOIN 
    (SELECT CCFO_CFO, DESC_CFO FROM BENTIVI.CFO) CFO ON CFO.CCFO_CFO = PED.CCFO_CFO    
LEFT JOIN 
    (SELECT CODI_PES, NOME_PES FROM BENTIVI.PESSOAL) PES ON PES.CODI_PES = PED.CODI_PES     
LEFT JOIN 
    (SELECT CODI_TOP, DESC_TOP FROM BENTIVI.TIPOOPER) TOP ON TOP.CODI_TOP = PED.CODI_TOP
LEFT JOIN 
    (SELECT 
        VLR.CODI_IND, VLR.CODI_EMP, VLR.DATA_VLR, VLR.VLOR_VLR, IND.DESC_IND  
      FROM BENTIVI.INDVALOR VLR
      INNER JOIN BENTIVI.INDEXADOR IND ON IND.CODI_IND = VLR.CODI_IND  ) VLR ON VLR.CODI_EMP = PED.CODI_EMP AND
                                                               VLR.CODI_IND = PED.CODI_IND AND
                                                               VLR.DATA_VLR = PED.DATA_VLR
inner join 
    (SELECT  PSV.CODI_PSV, PSV.DESC_PSV, G.CODI_GPR, G.DESC_GPR, S.CODI_SBG, S.DESC_SBG, TRA.CODI_TRA, TRA.RAZA_TRA,
      PRI.CODI_PRI ||'-'|| PRI.DESC_PRI PRINCIPIO_ATIVO, PSV.UNID_PSV FROM BENTIVI.PRODSERV PSV 
     INNER JOIN BENTIVI.GRUPO G ON G.CODI_GPR = PSV.CODI_GPR         
     LEFT JOIN BENTIVI.SUBGRUPO S ON S.CODI_SBG = PSV.CODI_SBG AND S.CODI_GPR = PSV.CODI_GPR
     INNER JOIN BENTIVI.PRODUTO PRO ON PRO.CODI_PSV = PSV.CODI_PSV
     LEFT JOIN BENTIVI.PRINATIVOS PRI ON (PRI.CODI_PRI = psv.CODI_PRI)
     LEFT JOIN BENTIVI.TRANSAC TRA ON TRA.CODI_TRA = PRO.CODI_TRA) PSV ON PSV.CODI_PSV = PED.CODI_PSV
LEFT JOIN 
    (SELECT TABE_CTA, DESC_CTA FROM BENTIVI.CABTAB) CTA ON CTA.TABE_CTA = PED.TABE_CTA
LEFT JOIN 
    BENTIVI.NEGOCIACAO NEG ON NEG.CTRL_NEG = PED.CTRL_NEG AND
                      NEG.CODI_EMP = PED.CODI_EMP AND
                      NEG.CODI_PES = PED.COD1_PES
left join 
    BENTIVI.indvalor vneg on vneg.codi_emp = neg.codi_emp and
                     vneg.codi_ind = neg.codi_ind and
                     vneg.data_vlr = neg.data_vlr
LEFT JOIN 
    (SELECT USU.CODI_USU, PES.CODI_PES, PES.NOME_PES 
     FROM BENTIVI.PESSOAL PES 
     INNER JOIN BENTIVI.CADUSU USU ON USU.CODI_PES = PES.CODI_PES) USU ON USU.CODI_USU = PED.CODI_USU
WHERE PED.DEMI_PED between (TO_DATE('01/01/2024', 'DD/MM/YYYY')) and (TO_DATE('31/12/2030', 'DD/MM/YYYY'))