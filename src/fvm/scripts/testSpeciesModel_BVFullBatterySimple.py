import sys
sys.setdlopenflags(0x100|0x2)

import fvm.fvmbaseExt as fvmbaseExt
import fvm.importers as importers
import fvm.models_atyped_double as models
import fvm.exporters_atyped_double as exporters
from FluentCase import FluentCase
#fvmbaseExt.enableDebug("cdtor")
import time

reader = FluentCase("../test/FullBatterySimple.cas")
reader.read();
meshes_case = reader.getMeshList()

# add double shell to mesh between two materials
# When creating double shell mesh, the mesh it is created from
# is called the 'parent' mesh and the mesh that is passed as an argument
# is called the 'other' mesh
#
# parent has to be electrolyte, other has to be solid electrode 
# for B-V equations to work

#interfaceID1 = 11
shellMeshAnode = meshes_case[2].createDoubleShell(6, meshes_case[1], 17)
#interfaceID2 = 17
shellMeshCathode = meshes_case[2].createDoubleShell(5, meshes_case[0], 16)


meshes = [meshes_case[0], meshes_case[1], meshes_case[2], shellMeshAnode, shellMeshCathode]
CathodeShellMeshID = 4
AnodeShellMeshID = 3
ElectrolyteMeshID = 2

geomFields =  models.GeomFields('geom')
metricsCalculator = models.MeshMetricsCalculatorA(geomFields,meshes)

metricsCalculator.init()

nSpecies = 1

timeStep = 2.5
numTimeSteps = 2500
numIterPerTimeStep = 10000 # nonlinear so multiple iterations per timestep needed
TimestepTolerance = 1.0e-8
MinimumIterationsPerTimeStep = 60
FluxBalanceTolerance = 1.0e-5

AppliedCurrent = 0.4e-3 #in Amps
D_cathode = 1.0e-13 #m^2/s
D_electrolyte = 2.66e-9 #m^2/s
D_anode = 5.0e-12 #m^2/s
k_cathode = 4.29e11 #Siemens/m
k_electrolyte = 2.825e11 #Siemens/m
k_anode = 1.1166e11 #Siemens/m
BVReactionRateConstant = 5.0e-9 # m/s
FluxArea = 20.0e-6 #m^2
PotentialFlux = AppliedCurrent/FluxArea # in A/m^2 or C/s/m^2

######################################################
## Species Model
######################################################
smodel = models.SpeciesModelA(geomFields,meshes,nSpecies)
bcmap = smodel.getBCMap(0)
vcmap = smodel.getVCMap(0)

vcCathode = vcmap[0]
vcSeparator = vcmap[2]
vcAnode = vcmap[1]

vcCathode['massDiffusivity'] = D_cathode
vcSeparator['massDiffusivity'] = D_electrolyte
vcAnode['massDiffusivity'] = D_anode

bcLeftTop = bcmap[12]
bcLeftMiddle = bcmap[11]
bcTop1 = bcmap[8]
bcBottom1 = bcmap[7]
bcRightTop = bcmap[10]
bcRightMiddle = bcmap[9]


#Zero Flux on Left,Right
#bcLeftTop.bcType = 'SpecifiedMassFraction'
#bcRight.bcType = 'SpecifiedMassFraction'
#bcLeftTop.setVar('specifiedMassFraction', 1.0)
#bcRight.setVar('specifiedMassFraction', 1000.0)
bcLeftTop.bcType = 'SpecifiedMassFlux'
bcLeftTop.setVar('specifiedMassFlux', 0.0)
bcRightTop.bcType = 'SpecifiedMassFlux'
bcRightTop.setVar('specifiedMassFlux', 0.0)
bcLeftMiddle.bcType = 'SpecifiedMassFlux'
bcLeftMiddle.setVar('specifiedMassFlux', 0.0)
bcRightMiddle.bcType = 'SpecifiedMassFlux'
bcRightMiddle.setVar('specifiedMassFlux', 0.0)

# Neumann on Bottom,Top
bcBottom1.bcType = 'SpecifiedMassFlux'
bcBottom1.setVar('specifiedMassFlux', 0.0)
bcTop1.bcType = 'SpecifiedMassFlux'
bcTop1.setVar('specifiedMassFlux', 0.0)

soptions = smodel.getOptions()
soptions.transient = True
soptions.setVar('timeStep',timeStep)


vcCathode['initialMassFraction'] = 3900
vcSeparator['initialMassFraction'] = 4115
vcAnode['initialMassFraction'] = 18000

#soptions.setVar('initialMassFraction0',3900)
#soptions.setVar('initialMassFraction1',14870)
#soptions.setVar('initialMassFraction2',4115) 

# A = Phi_S    B = Phi_E
#soptions.setVar('A_coeff',0.72)
#soptions.setVar('B_coeff',0.42)
soptions.ButlerVolmer = True
soptions.setVar('ButlerVolmerRRConstant',BVReactionRateConstant)
soptions.setVar('interfaceUnderRelax',1.0)
soptions.setVar('ButlerVolmerAnodeShellMeshID',AnodeShellMeshID)
soptions.setVar('ButlerVolmerCathodeShellMeshID',CathodeShellMeshID)

solver = fvmbaseExt.BCGStab()
pc = fvmbaseExt.JacobiSolver()
pc.verbosity=0
solver.preconditioner = pc
solver.relativeTolerance = 1e-14 #solver tolerance
solver.absoluteTolerance = 1e-14 #solver tolerance
solver.nMaxIterations = 3
solver.maxCoarseLevels=30
solver.verbosity=0
soptions.linearSolver = solver
soptions.relativeTolerance=1e-14 #model tolerance
soptions.absoluteTolerance=1e-14 #model tolerance

######################################################
## Potential Model
######################################################

elecFields = models.ElectricFields('elec')
emodel = models.ElectricModelA(geomFields,elecFields,meshes)
bcmap2 = emodel.getBCMap()
vcmap2 = emodel.getVCMap()

vcCathode2 = vcmap2[0]
vcSeparator2 = vcmap2[2]
vcAnode2 = vcmap2[1]

vcCathode2['dielectric_constant'] = k_cathode
vcSeparator2['dielectric_constant'] = k_electrolyte
vcAnode2['dielectric_constant'] = k_anode

bcLeftTop_2 = bcmap2[12]
bcLeftMiddle_2 = bcmap2[11]
bcTop1_2 = bcmap2[8]
bcBottom1_2 = bcmap2[7]
bcRightTop_2 = bcmap2[10]
bcRightMiddle_2 = bcmap2[9]

#Dirichlet on Left,Right
#bcRighte.bcType = 'SpecifiedPotential'
#bcRighte.setVar('specifiedPotential', 0.0)
bcRightTop_2.bcType = 'SpecifiedPotentialFlux'
bcRightTop_2.setVar('specifiedPotentialFlux', 0.0)
bcRightMiddle_2.bcType = 'SpecifiedPotentialFlux'
bcRightMiddle_2.setVar('specifiedPotentialFlux', -1*PotentialFlux)
#bcRightMiddle_2.setVar('specifiedPotentialFlux', 0.0)

bcLeftTop_2.bcType = 'SpecifiedPotentialFlux'
bcLeftTop_2.setVar('specifiedPotentialFlux', 0.0)
bcLeftMiddle_2.bcType = 'SpecifiedPotential'
bcLeftMiddle_2.setVar('specifiedPotential', 0.0)
#bcLeftMiddle_2.bcType = 'SpecifiedPotentialFlux'
#bcLeftMiddle_2.setVar('specifiedPotentialFlux', PotentialFlux)

# Neumann on Bottom,Top
bcBottom1_2.bcType = 'SpecifiedPotentialFlux'
bcBottom1_2.setVar('specifiedPotentialFlux', 0.0)
bcTop1_2.bcType = 'SpecifiedPotentialFlux'
bcTop1_2.setVar('specifiedPotentialFlux', 0.0)

eoptions = emodel.getOptions()
eoptions.ButlerVolmer = True
eoptions.setVar('ButlerVolmerRRConstant',BVReactionRateConstant)
eoptions.setVar('ButlerVolmerAnodeShellMeshID',AnodeShellMeshID)
eoptions.setVar('ButlerVolmerCathodeShellMeshID',CathodeShellMeshID)
eoptions.setVar('BatteryElectrolyteMeshID',ElectrolyteMeshID)

# A = c_S    B = c_E
#eoptions.setVar('Interface_A_coeff',14780)
#eoptions.setVar('Interface_B_coeff',2000)

solver = fvmbaseExt.BCGStab()
pc = fvmbaseExt.JacobiSolver()
pc.verbosity=0
solver.preconditioner = pc
solver.relativeTolerance = 1e-14 #solver tolerance
solver.absoluteTolerance = 1e-14 #solver tolerance
solver.nMaxIterations = 100
solver.maxCoarseLevels=30
solver.verbosity=0
eoptions.electrostaticsLinearSolver = solver
eoptions.electrostaticsTolerance=1e-40 #model tolerance
eoptions.chargetransportTolerance=1e-40 #model tolerance

eoptions.chargetransport_enable = False
eoptions.setVar('initialPotential',0.0)

################################################
######## Solve coupled system         ##########
################################################

def advanceUnsteady(smodel,emodel,elecFields,geomFields,meshes,numTimeSteps,numIterPerTimeStep,TimestepTolerance):

   outputFile = open('./outputFile.txt', 'w++')
   outputFile.write('TimeStep(' + str(timeStep) + 'seconds) ConvergenceTime(s) Iterations(Max=' + str(numIterPerTimeStep) + ') FinalResidual FluxBalance\n')
   outputFile.close()

   for t in range(1,(numTimeSteps+1)):
     
     TimestepStart = time.clock()

     for i in range(0,numIterPerTimeStep):

        # set the species concentrations for the species of interest (Lithium)
        elecFields.speciesConcentration = speciesFields.massFraction

        emodel.advance(20)

        #set the potential and mass fraction that the potentail model saw, for all species   
        for j in range(0,nSpecies):
           sFields = smodel.getSpeciesFields(j)
           sFields.elecPotential = elecFields.potential
           sFields.massFractionElectricModel = sFields.massFraction###
        
        smodel.advance(1)

        #exit if residual is NAN or less than Tolerance
        if (not(smodel.getMassFractionResidual(0) > TimestepTolerance)):
           #exit only if minimum number of iterations have been run 
           #and flux balance has been reached
           FluxBalance = smodel.getMassFluxIntegral(meshes[1],17,0) + smodel.getMassFluxIntegral(meshes[0],16,0)
	   if (((i+2)>MinimumIterationsPerTimeStep)&(abs(FluxBalance)<FluxBalanceTolerance)):
              break

	#exit immediately if residual is NAN, regardless of iteration count
        if ((not(smodel.getMassFractionResidual(0) <= TimestepTolerance))&(not(smodel.getMassFractionResidual(0) > TimestepTolerance))):
           break


     #print flux balances
     print "Fluxes:"
     mesh = meshes[1] #anode
     massFlux1 = smodel.getMassFluxIntegral(mesh,11,0)
     massFlux2 = smodel.getMassFluxIntegral(mesh,17,0)
     print massFlux1
     print massFlux2
     mesh = meshes[0] #cathode
     massFlux3 = smodel.getMassFluxIntegral(mesh,9,0)
     massFlux4 = smodel.getMassFluxIntegral(mesh,16,0)
     print massFlux3
     print massFlux4

     TimestepEnd = time.clock()
     outputFile = open('./outputFile.txt', 'a')
     outputFile.write(str(t) + ' ' + str(TimestepEnd - TimestepStart) + ' ' + str(i+1) + ' ' + str(smodel.getMassFractionResidual(0)) + ' ' + str(massFlux2+massFlux4) + '\n')
     outputFile.close()

     if ((not(smodel.getMassFractionResidual(0) <= TimestepTolerance))&(not(smodel.getMassFractionResidual(0) > TimestepTolerance))):
        # current residual must be NAN, so end simualation and do not write to .vtk file
        break

     filename = 'TimeStep_Species' + `t` + '.vtk'
     writer = exporters.VTKWriterA(geomFields,meshes_case,filename,
                                         "TestBV",False,0)
     writer.init()
     writer.writeScalarField((smodel.getSpeciesFields(0)).massFraction,"LiConc")
     writer.finish()

     filename2 = 'TimeStep_Electric' + `t` + '.vtk'
     writer2 = exporters.VTKWriterA(geomFields,meshes_case,filename2,
                                         "TestBV",False,0)
     writer2.init()
     writer2.writeScalarField(elecFields.potential,"ElecPotential")
     writer2.finish()

     print "#############################################################"
     print 'Finished time step %i in %i iterations and %f seconds' % (t,(i+1),(TimestepEnd - TimestepStart))
     print "#############################################################"
     smodel.updateTime()


# initialize
emodel.init()
smodel.init()

# initialize potential model to match with species model at time 0
speciesFields = smodel.getSpeciesFields(0)
elecFields.speciesConcentration = speciesFields.massFraction    
emodel.advance(200)

# write initial conditons
writer = exporters.VTKWriterA(geomFields,meshes_case,'TimeStep_Species0.vtk',
                              "TestBV",False,0)
writer.init()
writer.writeScalarField((smodel.getSpeciesFields(0)).massFraction,"LiConc")
writer.finish()
writer2 = exporters.VTKWriterA(geomFields,meshes_case,'TimeStep_Electric0.vtk',
                               "TestBV",False,0)
writer2.init()
writer2.writeScalarField(elecFields.potential,"ElecPotential")
writer2.finish()

# solve coupled system
advanceUnsteady(smodel,emodel,elecFields,geomFields,meshes,numTimeSteps,numIterPerTimeStep,TimestepTolerance)

'''
mesh = meshes[1]
massFlux = smodel.getMassFluxIntegral(mesh,6,0)
print massFlux
mesh = meshes[0]
massFlux2 = smodel.getMassFluxIntegral(mesh,5,0)
print massFlux2

mesh = meshes[0]
massFlux1 = smodel.getMassFluxIntegral(mesh,interfaceID,0)
print massFlux1
'''
