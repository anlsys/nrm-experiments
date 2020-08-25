let Cfg = ./Cfg.dhall

let Hint =
      < Full
      | Only :
          { only : List (List { actuatorID : Text, actuatorValue : Double }) }
      >

let LearnCfg =
      < Lagrange :
          { lagrange : Double }
      | Knapsack :
          { knapsack : Double }
      | Random :
          { random : Optional Integer }
      | Contextual :
          { contextual : { horizon : Integer } }
      >

let ControlCfg =
      < ControlCfg :
          { minimumControlInterval :
              { fromuS : Double }
          , staticPower :
              { fromuW : Double }
          , learnCfg :
              LearnCfg
          , speedThreshold :
              Double
          , referenceMeasurementRoundInterval :
              Integer
          , hint :
              Hint
          }
      | FixedCommand :
          { fixedPower : { fromuW : Double } }
      >

in      ../../hnrm/hsnrm/resources/defaults/Cfg.dhall
      ⫽ { controlCfg =
            ControlCfg.ControlCfg
            { minimumControlInterval =
                { fromuS = 1000000.0 }
            , staticPower =
                { fromuW = 2.0e8 }
            , learnCfg =
                LearnCfg.Contextual { contextual = { horizon = +111 } }
            , speedThreshold =
                0.9
            , referenceMeasurementRoundInterval =
                +6
            , hint =
                Hint.Only
                { only = [ [ { actuatorID = "toto", actuatorValue = 66.0 } ] ] }
            }
        , verbose =
            < Error | Info | Debug >.Info
        }
    : Cfg
