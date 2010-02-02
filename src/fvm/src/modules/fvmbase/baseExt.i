%module fvmbaseExt
%{
#define SWIG_FILE_WITH_INIT
  %}
%{
#include "CException.h"
#include <rlog/StdioNode.h>
#include <rlog/RLogChannel.h>
#include "AMG.h"
#include "BCGStab.h"
#include "ILU0Solver.h"
#include "JacobiSolver.h"
#include "ArrayBase.h"
#include "Array.h"
  
rlog::StdioNode *stdLog;
%}


%include "std_string.i"
%include "std_vector.i"
%include "std_except.i"
%include "std_map.i"
%include "std_set.i"


namespace std{
%template(vectorStr) vector<string>;
%template(vectorInt) vector<int>;
%template(IntSet)    set<int>;
 }


%exception {
    try {
        $action
    }
    catch (CException e) {
        SWIG_exception(SWIG_RuntimeError,e.what());
    }
    catch(...) {
        SWIG_exception(SWIG_RuntimeError,"Unknown exception");
    }
}

using namespace std;
%include "ArrayBase.i"
%include "Vector.i"

typedef Vector<double,3> VecD3;
%template(VecD3) Vector<double,3>;

%include "Field.i"
%include "CRConnectivity.i"
%include "Mesh.i"
%include "LinearSolver.i"
%include "AMG.i"
%include "BCGStab.i"
%include "JacobiSolver.i"

%include "CellMark.i"
%include "MPM_Particles.i"
%include "Octree.i"
%include "Grid.i"
%include "FVMParticles.i"
%include "MeshAssembler.i"
%include "ILU0Solver.i"

#ifdef FVM_PARALLEL

%include "StorageSiteMerger.i"
%include "LinearSystemMerger.i"
#endif


%inline %{
  void enableDebug(const string channel)
  {
          stdLog->subscribeTo(rlog::GetGlobalChannel(channel.c_str()));
  }

  boost::shared_ptr<ArrayBase> newIntArray(const int size)
  {
    return shared_ptr<ArrayBase>(new Array<int>(size));
  }
  
  %}

%init %{

  import_array();
stdLog = new rlog::StdioNode();

%}
