class BCGStab : public LinearSolver
{
public:

  BCGStab();
  
  LinearSolver *preconditioner;
};

