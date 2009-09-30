#include "BCGStab.h"

BCGStab::BCGStab() :
  preconditioner(0)
{}

BCGStab::~BCGStab()
{
}

void
BCGStab::cleanup()
{
  preconditioner->cleanup();
}

MFRPtr
BCGStab::solve(LinearSystem & ls)
{
  const MultiFieldMatrix& matrix = ls.getMatrix();

  // original system is in delta form
  shared_ptr<MultiField> x(ls.getDeltaPtr());
  shared_ptr<MultiField> bOrig(ls.getBPtr());
  
  matrix.computeResidual(ls.getDelta(),ls.getB(),ls.getResidual());

  MFRPtr rNorm0(ls.getResidual().getOneNorm());
  
  shared_ptr<MultiField> r(dynamic_pointer_cast<MultiField>(ls.getResidual().newCopy()));
  shared_ptr<MultiField> rTilda(dynamic_pointer_cast<MultiField>(ls.getResidual().newCopy()));

  shared_ptr<MultiField> p;
  shared_ptr<MultiField> pHat(dynamic_pointer_cast<MultiField>(x->newClone()));
  shared_ptr<MultiField> v(dynamic_pointer_cast<MultiField>(x->newClone()));
  shared_ptr<MultiField> t(dynamic_pointer_cast<MultiField>(x->newClone()));

  MFRPtr rho;
  MFRPtr rhoPrev;

  MFRPtr alpha;
  MFRPtr omega;

  if (verbosity >0)
    cout << 0 << ": " << *rNorm0 << endl;

  for(int i = 0; i<nMaxIterations; i++)
  {
      rhoPrev = rho;
      rho = r->dotWith(*rTilda);

      rho->reduceSum();

      if (!p)
      {
          p = dynamic_pointer_cast<MultiField>(r->newCopy());
      }
      else
      {
          MFRPtr rhoRatio = (*rho) / (*rhoPrev);
          MFRPtr alphaByOmega = (*alpha) / (*omega);
          MFRPtr beta = (*rhoRatio) * (*alphaByOmega);
          p->msaxpy(*omega,*v);
          *p *= *beta;
          *p += *r;
      }

      pHat->zero();
      ls.replaceDelta(pHat);
      ls.replaceB(p);
      
      preconditioner->smooth(ls);

      matrix.multiply(*v,*pHat);
#ifdef FVM_PARALLEL
      pHat->sync();
#endif

      MFRPtr rtv = rTilda->dotWith(*v);
      rtv->reduceSum();

      alpha = (*rho)/(*rtv);

      x->msaxpy(*alpha,*pHat);
      r->msaxpy(*alpha,*v);
      
      MFRPtr rNorm = r->getOneNorm();

      if (*rNorm < absoluteTolerance)
      {
          cout << "converged with small r " << endl;
          break;
      }

      shared_ptr<MultiField> sHat = pHat;
      sHat->zero();
      ls.replaceDelta(sHat);
      ls.replaceB(r);
      
      preconditioner->smooth(ls);

      matrix.multiply(*t,*sHat);
#ifdef FVM_PARALLEL
      sHat->sync();
#endif

      MFRPtr tdotr = t->dotWith(*r);
      MFRPtr tdott = t->dotWith(*t);

      tdotr->reduceSum();
      tdott->reduceSum();

      omega = (*tdotr) / (*tdott);

      x->msaxpy(*omega,*sHat);
      r->msaxpy(*omega,*t);

      rNorm = r->getOneNorm();

      MFRPtr normRatio((*rNorm)/(*rNorm0));
      if (verbosity >0)
        cout << i+1 << ": " << *rNorm << endl;
      if (*rNorm < absoluteTolerance || *normRatio < relativeTolerance)
        break;
    
            
  }
  ls.replaceDelta(x);
  ls.replaceB(bOrig);

  matrix.computeResidual(ls.getDelta(),ls.getB(),ls.getResidual());
  MFRPtr rNormn(ls.getResidual().getOneNorm());
  if (verbosity >0)
    cout << "n" << ": " << *rNormn << endl;
  
  return rNorm0;
}

void
BCGStab::smooth(LinearSystem& ls)
{
  throw CException("cannot use BCGStab as preconditioner");
}
